from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from apps.research_candidates.models import ResearchCandidate, Notification
from apps.research_candidates.tasks import run_match_for_research_task, run_match_for_researcher_task, send_notification_email_task
from django.conf import settings

@receiver(post_save, sender=Notification)
def send_notification_email(sender, instance, created, **kwargs):
    """
    Envia email quando uma notificação é criada.
    Despachado de forma assíncrona via Celery.
    """
    if created:
        # Verifica se email notifications estão habilitadas
        if getattr(settings, 'SEND_NOTIFICATION_EMAILS', True):
            send_notification_email_task.delay(instance.id)

@receiver(post_save, sender=ResearchCandidate)
def handle_research_candidate_lifecycle(sender, instance, created, **kwargs):
    """
    Handler consolidado para todos os eventos do lifecycle de ResearchCandidate.
    Cria notificações apropriadas e dispara matching IA se necessário.
    """

    # ==== PROPOSTA MANUAL CRIADA ====
    if created and instance.source == 'manual':
        _notify_company_on_proposal_received(instance)
        return

    # ==== STATUS MUDOU (proposta ou match automático) ====
    if not created and instance.source == 'manual':
        _notify_researcher_on_status_changed(instance)

    # ==== MATCH AUTOMÁTICO CRIADO ====
    if created and instance.source == 'ai':
        _notify_researcher_on_ai_match(instance)
        return


def _notify_company_on_proposal_received(candidate):
    """Notifica empresa quando pesquisador envia proposta"""
    empresa = candidate.research.company
    pesquisador = candidate.researcher

    if not empresa.user:
        return

    Notification.objects.create(
        user=empresa.user,
        tipo='proposta_recebida',
        titulo=f'Nova proposta para {candidate.research.title}',
        mensagem=f'{pesquisador.name} enviou uma proposta para seu desafio "{candidate.research.title}"',
        research_candidate=candidate
    )


def _notify_researcher_on_status_changed(candidate):
    """Notifica pesquisador quando status de proposta manual muda"""
    pesquisador = candidate.researcher

    if not pesquisador.user:
        return

    status_labels = {
        'interested': 'Interessada',
        'under_review': 'Em Revisão',
        'approved': 'Aprovada',
        'rejected': 'Recusada',
    }

    status_msg = status_labels.get(candidate.status, candidate.status)

    Notification.objects.create(
        user=pesquisador.user,
        tipo='status_alterado',
        titulo=f'Proposta {status_msg.lower()}',
        mensagem=f'Sua proposta para "{candidate.research.title}" foi {status_msg.lower()}',
        research_candidate=candidate
    )


def _notify_researcher_on_ai_match(candidate):
    """Notifica pesquisador quando matching IA o sugere para uma pesquisa"""
    pesquisador = candidate.researcher

    if not pesquisador.user:
        return

    score_percent = int(float(candidate.score_match or 0) * 100) if candidate.score_match else 0

    Notification.objects.create(
        user=pesquisador.user,
        tipo='novo_match_disponivel',
        titulo=f'Nova oportunidade de pesquisa: {candidate.research.title}',
        mensagem=f'Sistema encontrou compatibilidade {score_percent}% com sua expertise em "{candidate.research.title}"',
        research_candidate=candidate
    )


@receiver(post_save, sender=ResearchCandidate)
def trigger_ai_matching(sender, instance, created, **kwargs):
    """
    Dispara matching automático quando research ou researcher é criado/modificado.
    Este é um signal separado para não conflitar com notificações.
    """
    if not created:
        return

    # Só dispara para matches manuais ou quando habilitado via config
    if instance.source == 'manual':
        return

    # Se AI matching está habilitado, dispara a task
    if getattr(settings, 'AI_MATCH_ASYNC_ENABLED', False):
        if instance.source == 'ai':
            # Task já foi disparada pelo signal da Research/Researcher
            # Este signal evita re-disparo
            pass

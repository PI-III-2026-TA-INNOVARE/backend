from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from apps.research_candidates.models import ResearchCandidate
from apps.research_candidates.tasks import send_notification_email_task

@receiver(pre_save, sender=ResearchCandidate)
def track_candidate_status_before_save(sender, instance, **kwargs):
    """Armazena o status anterior para detectar mudancas no post_save."""
    if instance.pk:
        try:
            old_instance = ResearchCandidate.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except ResearchCandidate.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=ResearchCandidate)
def handle_research_candidate_lifecycle(sender, instance, created, **kwargs):
    """
    Handler consolidado para todos os eventos do lifecycle de ResearchCandidate.
    Dispara notificacoes por email e persiste notificacoes para a API.
    """
    if created and instance.source in ['manual', 'interest']:
        _notify_company_on_proposal_received(instance)
        return

    if created and instance.source == 'ai':
        _notify_researcher_on_ai_match(instance)
        return

    if not created:
        old_status = getattr(instance, '_old_status', None)
        if old_status and old_status != instance.status:
            _notify_researcher_on_status_changed(instance)


def _notify_company_on_proposal_received(candidate):
    """Notifica empresa quando pesquisador envia proposta ou demonstra interesse."""
    empresa = candidate.research.company
    pesquisador = candidate.researcher

    if not empresa.user:
        return

    action_text = "enviou uma proposta" if candidate.source == 'manual' else "demonstrou interesse"
    titulo = f'Nova interacao em: {candidate.research.title}'
    mensagem = f'{pesquisador.name} {action_text} para seu desafio "{candidate.research.title}"'
    
    send_notification_email_task.delay(
        user_id=empresa.user.id_user,
        tipo='proposta_recebida',
        titulo=titulo,
        mensagem=mensagem,
        candidate_id=candidate.id_candidate
    )


def _notify_researcher_on_status_changed(candidate):
    """Notifica pesquisador quando status de sua candidatura muda."""
    pesquisador = candidate.researcher

    if not pesquisador.user:
        return

    status_labels = {
        'suggested': 'Sugerida',
        'interested': 'Interessada',
        'under_review': 'Em Revisao',
        'approved': 'Aprovada',
        'rejected': 'Recusada',
    }

    status_msg = status_labels.get(candidate.status, candidate.status)
    titulo = f'Atualizacao: {candidate.research.title}'
    mensagem = f'O status da sua participacao em "{candidate.research.title}" mudou para: {status_msg}'

    send_notification_email_task.delay(
        user_id=pesquisador.user.id_user,
        tipo='status_alterado',
        titulo=titulo,
        mensagem=mensagem,
        candidate_id=candidate.id_candidate
    )


def _notify_researcher_on_ai_match(candidate):
    """Notifica pesquisador quando matching IA o sugere para uma pesquisa."""
    pesquisador = candidate.researcher

    if not pesquisador.user:
        return

    score_percent = int(float(candidate.score_match or 0) * 100) if candidate.score_match else 0
    titulo = f'Nova oportunidade de pesquisa: {candidate.research.title}'
    mensagem = f'Sistema encontrou compatibilidade {score_percent}% com sua expertise em "{candidate.research.title}"'

    send_notification_email_task.delay(
        user_id=pesquisador.user.id_user,
        tipo='novo_match',
        titulo=titulo,
        mensagem=mensagem,
        candidate_id=candidate.id_candidate
    )


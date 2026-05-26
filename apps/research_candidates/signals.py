from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.research_candidates.models import ResearchCandidate, Notification

@receiver(post_save, sender=ResearchCandidate)
def notify_on_proposal_created(sender, instance, created, **kwargs):
    """Cria notificação quando pesquisador envia proposta (manual)"""
    if created and instance.source == 'manual':
        empresa = instance.research.company
        pesquisador = instance.researcher
        
        if not empresa.user:
            return
        
        # Notifica a empresa
        Notification.objects.create(
            user=empresa.user,
            tipo='proposta_recebida',
            titulo=f'Nova proposta para {instance.research.title}',
            mensagem=f'{pesquisador.name} enviou uma proposta para seu desafio "{instance.research.title}"',
            research_candidate=instance
        )

@receiver(post_save, sender=ResearchCandidate)
def notify_on_status_changed(sender, instance, created, **kwargs):
    """Cria notificação quando status da proposta muda"""
    if not created and instance.source == 'manual':
        pesquisador = instance.researcher
        
        if not pesquisador.user:
            return
        
        status_labels = {
            'interested': 'Interessada',
            'under_review': 'Em Revisão',
            'approved': 'Aprovada',
            'rejected': 'Recusada',
        }
        
        status_msg = status_labels.get(instance.status, instance.status)
        
        # Notifica o pesquisador
        Notification.objects.create(
            user=pesquisador.user,
            tipo='status_alterado',
            titulo=f'Proposta {status_msg.lower()}',
            mensagem=f'Sua proposta para "{instance.research.title}" foi {status_msg.lower()}',
            research_candidate=instance
        )


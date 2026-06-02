from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from apps.research_candidates.services import run_match_for_research, run_match_for_researcher
from apps.research_candidates.models import Notification

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def run_match_for_research_task(self, research_id):
    return run_match_for_research(research_id)

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def run_match_for_researcher_task(self, researcher_id):
    return run_match_for_researcher(researcher_id)

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 2})
def send_notification_email_task(self, notification_id):
    """
    Envia email de notificação para o usuário.
    Disparada automaticamente quando uma notificação é criada.
    """
    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return {'status': 'error', 'message': 'Notificação não encontrada'}

    user = notification.user

    # Templates por tipo de notificação
    templates = {
        'proposta_recebida': 'emails/notification_proposal_received.html',
        'status_alterado': 'emails/notification_status_changed.html',
        'match_automatico': 'emails/notification_ai_match.html',
        'novo_match_disponivel': 'emails/notification_new_match.html',
        'deadline_proximo': 'emails/notification_deadline.html',
        'feedback_recebido': 'emails/notification_feedback.html',
        'pesquisa_atualizada': 'emails/notification_research_updated.html',
        'pesquisa_encerrada': 'emails/notification_research_closed.html',
    }

    template_name = templates.get(notification.tipo, 'emails/notification_default.html')

    try:
        context = {
            'notification': notification,
            'user': user,
            'title': notification.titulo,
            'message': notification.mensagem,
            'frontend_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:5173'),
        }

        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=notification.titulo,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@pdconnect.com'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return {'status': 'success', 'message': f'Email enviado para {user.email}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

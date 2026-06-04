from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from apps.research_candidates.services import run_match_for_research, run_match_for_researcher
from apps.users.models import User
from apps.notifications.models import Notification

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def run_match_for_research_task(self, research_id):
    return run_match_for_research(research_id)

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def run_match_for_researcher_task(self, researcher_id):
    return run_match_for_researcher(researcher_id)

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 2})
def send_notification_email_task(self, user_id, tipo, titulo, mensagem, candidate_id=None):
    """
    Persiste a notificacao no banco de dados e envia email de notificacao para o usuario.
    """
    try:
        user = User.objects.get(id_user=user_id)
    except User.DoesNotExist:
        return {'status': 'error', 'message': 'Usuario nao encontrado'}

    # 1. Persiste no banco para a API
    try:
        Notification.objects.create(
            user=user,
            type=tipo,
            title=titulo,
            message=mensagem,
            related_id=candidate_id
        )
    except Exception as e:
        print(f"Erro ao salvar notificacao no banco: {str(e)}")

    # 2. Prepara e envia o email
    if not getattr(settings, 'SEND_NOTIFICATION_EMAILS', True):
        return {'status': 'success', 'message': 'Notificacao salva no banco (email desativado)'}
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

    template_name = templates.get(tipo, 'emails/notification_default.html')

    try:
        context = {
            'user': user,
            'title': titulo,
            'message': mensagem,
            'candidate_id': candidate_id,
            'frontend_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:5173'),
        }

        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=titulo,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@pdconnect.com'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return {'status': 'success', 'message': f'Email enviado para {user.email}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


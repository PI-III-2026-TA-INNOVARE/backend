from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse


def send_password_reset_email(user_email, reset_token, frontend_url=None):
    """
    Envia email com link de redefinição de senha.

    Args:
        user_email: Email do usuário
        reset_token: Token de redefinição
        frontend_url: URL base do frontend para construir o link (ex: http://localhost:5173)
    """
    if not frontend_url:
        frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:5173'

    reset_link = f"{frontend_url}/reset-password?token={reset_token.token}"

    subject = "Redefinição de Senha - P&D Connect"
    message = f"""
Olá,

Você solicitou a redefinição de senha da sua conta no P&D Connect.

Clique no link abaixo para redefinir sua senha:
{reset_link}

Este link é válido por 24 horas.

Se você não solicitou a redefinição de senha, ignore este email.

Atenciosamente,
P&D Connect
    """

    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Redefinição de Senha - P&D Connect</h2>
            <p>Olá,</p>
            <p>Você solicitou a redefinição de senha da sua conta no P&D Connect.</p>
            <p>
                <a href="{reset_link}" style="background-color: #4CAF50; color: white; padding: 12px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
                    Redefinir Senha
                </a>
            </p>
            <p>Ou copie e cole este link no seu navegador:</p>
            <p>{reset_link}</p>
            <p><small>Este link é válido por 24 horas.</small></p>
            <p><small>Se você não solicitou a redefinição de senha, ignore este email.</small></p>
            <p>Atenciosamente,<br>P&D Connect</p>
        </body>
    </html>
    """

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        html_message=html_message,
        fail_silently=False,
    )

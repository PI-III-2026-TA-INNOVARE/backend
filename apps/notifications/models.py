from django.db import models
from django.conf import settings


class Notification(models.Model):
    id_notification = models.AutoField(primary_key=True, db_column='id_notificacao')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_column='id_usuario',
    )
    type = models.CharField(max_length=50, db_column='tipo')
    title = models.CharField(max_length=255, db_column='titulo')
    message = models.TextField(db_column='mensagem')
    is_read = models.BooleanField(default=False, db_column='lida')
    created_at = models.DateTimeField(auto_now_add=True, db_column='dt_criacao')
    related_id = models.IntegerField(blank=True, null=True, db_column='id_relacionado')

    class Meta:
        db_table = 'notificacao'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} - {self.title}'

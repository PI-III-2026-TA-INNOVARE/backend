from django.db import models
from django.conf import settings


class Notification(models.Model):
    id_notification = models.AutoField(primary_key=True, db_column='id')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_column='user_id',
    )
    type = models.CharField(max_length=20, db_column='tipo')
    title = models.CharField(max_length=200, db_column='titulo')
    message = models.TextField(db_column='mensagem')
    is_read = models.BooleanField(default=False, db_column='lido')
    created_at = models.DateTimeField(auto_now_add=True, db_column='data_criacao')
    read_at = models.DateTimeField(null=True, blank=True, db_column='data_leitura')
    related_id = models.IntegerField(blank=True, null=True, db_column='research_candidate_id')

    class Meta:
        db_table = 'notificacao'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} - {self.title}'

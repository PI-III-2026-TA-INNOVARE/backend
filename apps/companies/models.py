from django.db import models
from django.conf import settings

class Company(models.Model):
    id_company = models.AutoField(primary_key=True, db_column='id_empresa')
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='company_profile',
        db_column='id_usuario',
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=200, db_column='nome')
    cnpj = models.CharField(max_length=18, unique=True)
    registration_status = models.CharField(max_length=20, blank=True, null=True, db_column='situacao_cadastral')
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'empresa'

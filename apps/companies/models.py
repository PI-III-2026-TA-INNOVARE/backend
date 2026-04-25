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
    name = models.CharField(max_length=200, db_column='nome', blank=True, null=True)
    cnpj = models.CharField(max_length=18, unique=True)
    registration_status = models.CharField(max_length=20, blank=True, null=True, db_column='situacao_cadastral')
    legal_name = models.CharField(max_length=255, db_column='razao_social', blank=True, null=True)
    city = models.CharField(max_length=120, db_column='municipio', blank=True, null=True)
    state = models.CharField(max_length=2, db_column='uf', blank=True, null=True)
    street = models.CharField(max_length=255, db_column='logradouro', blank=True, null=True)
    number = models.CharField(max_length=20, db_column='numero', blank=True, null=True)
    complement = models.CharField(max_length=255, db_column='complemento', blank=True, null=True)
    neighborhood = models.CharField(max_length=120, db_column='bairro', blank=True, null=True)
    zip_code = models.CharField(max_length=8, db_column='cep', blank=True, null=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.legal_name or self.name or self.cnpj
    
    class Meta:
        db_table = 'empresa'

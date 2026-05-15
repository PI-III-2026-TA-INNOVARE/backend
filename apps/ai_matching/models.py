from django.db import models
from django.conf import settings
from apps.researchers.models import Researcher
from apps.companies.models import Company


class MatchingProfile(models.Model):
    """
    Perfil de busca e preferências para matching inteligente.
    Pode ser criado por pesquisadores ou empresas para definir preferências de match.
    """
    PROFILE_TYPE_CHOICES = [
        ('researcher', 'Pesquisador'),
        ('company', 'Empresa'),
    ]
    
    id_profile = models.AutoField(primary_key=True, db_column='id_perfil')
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='matching_profile',
        db_column='id_usuario'
    )
    profile_type = models.CharField(
        max_length=20,
        choices=PROFILE_TYPE_CHOICES,
        db_column='tipo_perfil'
    )
    researcher = models.OneToOneField(
        Researcher,
        on_delete=models.CASCADE,
        related_name='matching_profile_researcher',
        db_column='id_pesquisador',
        blank=True,
        null=True
    )
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='matching_profile_company',
        db_column='id_empresa',
        blank=True,
        null=True
    )
    description = models.TextField(
        db_column='descricao',
        help_text="Descrição das competências, necessidades ou expectativas"
    )
    keywords = models.TextField(
        db_column='palavras_chave',
        help_text="Palavras-chave separadas por vírgula"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='data_criacao')
    updated_at = models.DateTimeField(auto_now=True, db_column='data_atualizacao')
    is_active = models.BooleanField(default=True, db_column='ativo')
    
    def __str__(self):
        return f"{self.get_profile_type_display()} - {self.user.username}"
    
    class Meta:
        db_table = 'perfil_matching'
        verbose_name = 'Perfil de Matching'
        verbose_name_plural = 'Perfis de Matching'


class Match(models.Model):
    """
    Resultado de um matching inteligente entre pesquisadores e empresas.
    Armazena o score de compatibilidade e detalhes da análise.
    """
    MATCH_STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('accepted', 'Aceito'),
        ('rejected', 'Rejeitado'),
        ('contacted', 'Contatado'),
        ('in_progress', 'Em Andamento'),
        ('completed', 'Concluído'),
    ]
    
    id_match = models.AutoField(primary_key=True, db_column='id_matching')
    researcher = models.ForeignKey(
        Researcher,
        on_delete=models.CASCADE,
        related_name='matches_as_researcher',
        db_column='id_pesquisador'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='matches_as_company',
        db_column='id_empresa'
    )
    compatibility_score = models.FloatField(
        db_column='score_compatibilidade',
        help_text="Score de 0 a 100"
    )
    match_reason = models.TextField(
        db_column='motivo_matching',
        help_text="Explicação do matching gerada pela IA"
    )
    status = models.CharField(
        max_length=20,
        choices=MATCH_STATUS_CHOICES,
        default='pending',
        db_column='status'
    )
    search_query = models.TextField(
        db_column='query_busca',
        blank=True,
        null=True,
        help_text="Query original que gerou este match"
    )
    ai_analysis = models.JSONField(
        db_column='analise_ia',
        blank=True,
        null=True,
        help_text="Análise detalhada da IA em formato JSON"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='data_criacao')
    updated_at = models.DateTimeField(auto_now=True, db_column='data_atualizacao')
    
    def __str__(self):
        return f"Match: {self.researcher.name} - {self.company.name} ({self.compatibility_score}%)"
    
    class Meta:
        db_table = 'matching'
        verbose_name = 'Matching'
        verbose_name_plural = 'Matchings'
        unique_together = ('researcher', 'company')
        indexes = [
            models.Index(fields=['compatibility_score']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]


class MatchingHistory(models.Model):
    """
    Histórico de buscas e análises realizadas pela IA.
    Útil para auditoria e análise de padrões.
    """
    id_history = models.AutoField(primary_key=True, db_column='id_historico')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='matching_history',
        db_column='id_usuario'
    )
    search_query = models.TextField(
        db_column='query_busca',
        help_text="Texto enviado para busca inteligente"
    )
    query_type = models.CharField(
        max_length=20,
        choices=[
            ('find_companies', 'Encontrar Empresas'),
            ('find_researchers', 'Encontrar Pesquisadores'),
        ],
        db_column='tipo_query'
    )
    results_count = models.IntegerField(
        db_column='quantidade_resultados',
        default=0
    )
    ai_response = models.JSONField(
        db_column='resposta_ia',
        help_text="Resposta completa da IA"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='data_criacao')
    
    def __str__(self):
        return f"{self.get_query_type_display()} - {self.user.username}"
    
    class Meta:
        db_table = 'historico_matching'
        verbose_name = 'Histórico de Matching'
        verbose_name_plural = 'Históricos de Matching'
        ordering = ['-created_at']

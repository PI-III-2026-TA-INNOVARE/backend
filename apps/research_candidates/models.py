from django.db import models
from apps.research.models import Research     
from apps.researchers.models import Researcher
from django.conf import settings

class ResearchCandidate(models.Model):        
    class Source(models.TextChoices):
        AI = 'ai', 'ai'
        INTEREST = 'interest', 'interest'     
        MANUAL = 'manual', 'manual'

    class CandidateStatus(models.TextChoices):
        SUGGESTED = 'suggested', 'suggested'
        INTERESTED = 'interested', 'interested'
        UNDER_REVIEW = 'under_review', 'under_review'
        APPROVED = 'approved', 'approved'
        REJECTED = 'rejected', 'rejected'

    id_candidate = models.AutoField(primary_key=True, db_column='id_candidato')
    research = models.ForeignKey(Research, on_delete=models.CASCADE, related_name='candidates', db_column='id_pesquisa')
    researcher = models.ForeignKey(Researcher, on_delete=models.CASCADE, related_name='research_candidates', db_column='id_pesquisador')
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    score_match = models.DecimalField(max_digits=6, decimal_places=4, blank=True, null=True)
    status = models.CharField(max_length=20, choices=CandidateStatus.choices, default=CandidateStatus.SUGGESTED)
    interest_message = models.TextField(blank=True, null=True)
    match_reasons = models.JSONField(blank=True, null=True, db_column='motivos_match')
    score_features = models.JSONField(blank=True, null=True, db_column='features_score')
    ai_run_id = models.UUIDField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column='dt_cadastro')
    updated_at = models.DateTimeField(auto_now=True, db_column='dt_atualizacao')

    def __str__(self):
        return f'{self.research_id}:{self.researcher_id}'

    class Meta:
        db_table = 'pesquisa_candidato'
        constraints = [models.UniqueConstraint(fields=['research', 'researcher'], name='uq_pesquisa_candidato_pesquisa_pesquisador')]
        indexes = [models.Index(fields=['research', 'status'], name='idx_candidate_status'),
                   models.Index(fields=['research', 'source'], name='idx_candidate_source'),
                   models.Index(fields=['research', '-score_match'], name='idx_candidate_score')]

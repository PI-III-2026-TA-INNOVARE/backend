from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.conf import settings
from django.db import models
from pgvector.django import HnswIndex, VectorField

from apps.research.models import Research
from apps.researchers.models import Researcher

EMBEDDING_DIMENSION = getattr(settings, 'SEARCH_EMBEDDING_DIMENSION', 384)


class SearchResearcherIndex(models.Model):
    researcher = models.OneToOneField(
        Researcher,
        on_delete=models.CASCADE,
        related_name='search_index',
        db_column='id_pesquisador',
        primary_key=True,
    )
    search_text = models.TextField(blank=True, default='')
    search_tsv = SearchVectorField(null=True)
    embedding = VectorField(dimensions=EMBEDDING_DIMENSION, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'search_pesquisador'
        indexes = [
            GinIndex(fields=['search_tsv'], name='idx_search_pesq_tsv'),
            HnswIndex(
                name='idx_search_pesq_vec',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops'],
            ),
        ]


class SearchResearchIndex(models.Model):
    research = models.OneToOneField(
        Research,
        on_delete=models.CASCADE,
        related_name='search_index',
        db_column='id_pesquisa',
        primary_key=True,
    )
    search_text = models.TextField(blank=True, default='')
    search_tsv = SearchVectorField(null=True)
    embedding = VectorField(dimensions=EMBEDDING_DIMENSION, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'search_pesquisa'
        indexes = [
            GinIndex(fields=['search_tsv'], name='idx_search_pesquisa_tsv'),
            HnswIndex(
                name='idx_search_pesquisa_vec',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops'],
            ),
        ]

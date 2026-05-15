from rest_framework import serializers
from .models import MatchingProfile, Match, MatchingHistory
from apps.researchers.models import Researcher
from apps.companies.models import Company


class MatchingProfileSerializer(serializers.ModelSerializer):
    profile_type_display = serializers.CharField(
        source='get_profile_type_display',
        read_only=True
    )
    
    class Meta:
        model = MatchingProfile
        fields = [
            'id_profile',
            'user',
            'profile_type',
            'profile_type_display',
            'researcher',
            'company',
            'description',
            'keywords',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id_profile', 'created_at', 'updated_at']


class MatchSerializer(serializers.ModelSerializer):
    researcher_name = serializers.CharField(
        source='researcher.name',
        read_only=True
    )
    company_name = serializers.CharField(
        source='company.name',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    class Meta:
        model = Match
        fields = [
            'id_match',
            'researcher',
            'researcher_name',
            'company',
            'company_name',
            'compatibility_score',
            'match_reason',
            'status',
            'status_display',
            'search_query',
            'ai_analysis',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id_match',
            'researcher_name',
            'company_name',
            'created_at',
            'updated_at',
        ]


class MatchingHistorySerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source='user.username',
        read_only=True
    )
    query_type_display = serializers.CharField(
        source='get_query_type_display',
        read_only=True
    )
    
    class Meta:
        model = MatchingHistory
        fields = [
            'id_history',
            'user',
            'username',
            'search_query',
            'query_type',
            'query_type_display',
            'results_count',
            'ai_response',
            'created_at',
        ]
        read_only_fields = [
            'id_history',
            'username',
            'results_count',
            'created_at',
        ]


class SmartSearchRequestSerializer(serializers.Serializer):
    """Serializer para requisições de busca inteligente"""
    query = serializers.CharField(
        max_length=2000,
        help_text="Texto descritivo para busca inteligente"
    )
    search_type = serializers.ChoiceField(
        choices=['company', 'researcher'],
        help_text="Tipo de busca: 'company' para encontrar empresas, 'researcher' para encontrar pesquisadores"
    )
    limit = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=50,
        help_text="Limite de resultados"
    )
    threshold = serializers.FloatField(
        default=0.6,
        min_value=0.0,
        max_value=1.0,
        help_text="Score mínimo de compatibilidade (0-1)"
    )


class SmartSearchResponseSerializer(serializers.Serializer):
    """Serializer para resposta de busca inteligente"""
    matches = MatchSerializer(many=True)
    summary = serializers.CharField()
    ai_insights = serializers.JSONField()

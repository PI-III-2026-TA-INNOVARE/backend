from rest_framework import serializers
from apps.research_candidates.models import ResearchCandidate

class PropostaSerializer(serializers.ModelSerializer):
    """
    Serializer para propostas (usando tabela pesquisa_candidato).
    Uma proposta é um ResearchCandidate com source='manual'.
    """
    pesquisador_id = serializers.IntegerField(source='researcher.id_researcher', read_only=True)
    pesquisa_id = serializers.IntegerField(source='research.id_research', read_only=True)
    empresa_id = serializers.IntegerField(source='research.company.id_company', read_only=True)
    mensagem = serializers.CharField(source='interest_message')
    
    class Meta:
        model = ResearchCandidate
        fields = [
            'id_candidate',
            'pesquisador_id',
            'pesquisa_id',
            'empresa_id',
            'mensagem',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id_candidate', 'created_at', 'updated_at']

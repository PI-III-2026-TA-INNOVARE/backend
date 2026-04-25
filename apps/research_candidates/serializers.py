from rest_framework import serializers
from .models import ResearchCandidate

class ResearchCandidateSerializer(serializers.ModelSerializer):
    researcher_name = serializers.CharField(source='researcher.name', read_only=True)

    class Meta:
        model = ResearchCandidate
        fields = ['id_candidate', 'research', 'researcher', 'researcher_name', 'source', 'score_match', 'status', 'interest_message', 'ai_run_id', 'created_at', 'updated_at',]
        read_only_fields = ['created_at', 'updated_at', 'ai_run_id']

class ResearchCandidateStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearchCandidate
        fields = ['status']

    def validate_status(self, value):
        allowed = {ResearchCandidate.CandidateStatus.UNDER_REVIEW, ResearchCandidate.CandidateStatus.APPROVED, ResearchCandidate.CandidateStatus.REJECTED}
        if value not in allowed:
            raise serializers.ValidationError('Status inválido para ação da empresa. Use under_review, approved ou rejected.')
        return value

class ResearchInterestSerializer(serializers.Serializer):
    interest_message = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2000)

class ResearchMatchRunResponseSerializer(serializers.Serializer):
    research_id = serializers.IntegerField()
    job_id = serializers.UUIDField()
    status = serializers.CharField()

class ResearcherInterestListSerializer(serializers.ModelSerializer):
    research_id = serializers.IntegerField(source='research.id_research', read_only=True)
    research_title = serializers.CharField(source='research.title', read_only=True)

    class Meta:
        model = ResearchCandidate
        fields = ['id_candidate', 'research_id', 'research_title', 'source', 'score_match', 'status', 'interest_message', 'created_at', 'updated_at']
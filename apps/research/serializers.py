from rest_framework import serializers
from apps.research.models import Research

class ResearchSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(read_only=True)
    researcher = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Research
        fields = ['id_research', 'title', 'status', 'scope', 'goal', 'justification', 'results', 'deadline', 'budget', 'company', 'researcher', 'area', 'registration_date', 'update_date']
        read_only_fields = ['company', 'researcher', 'registration_date', 'update_date']

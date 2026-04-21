from rest_framework import serializers
from apps.research.models import Research

class ResearchSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Research
        fields = '__all__'

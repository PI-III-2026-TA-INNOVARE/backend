from rest_framework import serializers
from apps.research_area.models import ResearchArea

class ResearchAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearchArea
        fields = '__all__'
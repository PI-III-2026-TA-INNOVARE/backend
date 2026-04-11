from rest_framework import serializers
from apps.researchers.models import Researcher


class ResearcherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Researcher
        fields = '__all__'
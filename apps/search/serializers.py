from rest_framework import serializers


class SearchResearcherResultSerializer(serializers.Serializer):
    id_researcher = serializers.IntegerField()
    name = serializers.CharField()
    university = serializers.CharField(allow_null=True)
    availability = serializers.BooleanField(allow_null=True)
    score_hybrid = serializers.FloatField()
    score_semantic = serializers.FloatField()
    score_lexical = serializers.FloatField()


class SearchResearchResultSerializer(serializers.Serializer):
    id_research = serializers.IntegerField()
    title = serializers.CharField()
    status = serializers.CharField()
    area = serializers.CharField(allow_null=True)
    company = serializers.CharField(allow_null=True)
    score_hybrid = serializers.FloatField()
    score_semantic = serializers.FloatField()
    score_lexical = serializers.FloatField()

from rest_framework import generics
from apps.skills.models import Skill
from apps.skills.serializers import SkillSerializer


class SkillCreateListView(generics.ListCreateAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer

class SkillRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer

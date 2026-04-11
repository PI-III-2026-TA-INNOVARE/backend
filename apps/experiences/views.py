from rest_framework import generics
from apps.experiences.models import Experience
from apps.experiences.serializers import ExperienceSerializer


class ExperienceCreateListView(generics.ListCreateAPIView):
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer

class ExperienceRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer

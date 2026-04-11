from rest_framework import generics
from apps.researchers.models import Researcher
from apps.researchers.serializers import ResearcherSerializer


class ResearcherCreateListView(generics.ListCreateAPIView):
    queryset = Researcher.objects.all()
    serializer_class = ResearcherSerializer

class ResearcherRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Researcher.objects.all()
    serializer_class = ResearcherSerializer
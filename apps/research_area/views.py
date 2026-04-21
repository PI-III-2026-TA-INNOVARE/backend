from rest_framework import generics
from apps.research_area.models import ResearchArea
from apps.research_area.serializers import ResearchAreaSerializer


class ResearchAreaCreateListView(generics.ListCreateAPIView):
    queryset = ResearchArea.objects.all()
    serializer_class = ResearchAreaSerializer

class ResearchAreaRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = ResearchArea.objects.all()
    serializer_class = ResearchAreaSerializer

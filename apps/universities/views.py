from rest_framework import generics
from apps.universities.models import University
from apps.universities.serializers import UniversitySerializer


class UniversityCreateListView(generics.ListCreateAPIView):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer

class UniversityRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer

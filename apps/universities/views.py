from rest_framework import generics, permissions
from apps.universities.models import University
from apps.universities.serializers import UniversitySerializer


class UniversityCreateListView(generics.ListCreateAPIView):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [permissions.AllowAny]

class UniversityRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
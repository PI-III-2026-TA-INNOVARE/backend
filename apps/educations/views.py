from rest_framework import generics
from apps.educations.models import Education
from apps.educations.serializers import EducationSerializer


class EducationCreateListView(generics.ListCreateAPIView):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer

class EducationRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer

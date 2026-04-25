from rest_framework import generics
from django.shortcuts import get_object_or_404
from apps.resumes.models import Resume
from apps.resumes.serializers import ResumeSerializer

class ResumeCreateListView(generics.ListCreateAPIView):
    serializer_class = ResumeSerializer
    queryset = Resume.objects.prefetch_related('education', 'experience', 'skill').all()


class ResumeRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ResumeSerializer
    queryset = Resume.objects.prefetch_related('education', 'experience', 'skill').all()


class ResearcherResumeView(generics.RetrieveAPIView):
    serializer_class = ResumeSerializer

    def get_object(self):
        queryset = Resume.objects.prefetch_related('education', 'experience', 'skill')
        return get_object_or_404(queryset, researcher__id_researcher=self.kwargs['pk'])
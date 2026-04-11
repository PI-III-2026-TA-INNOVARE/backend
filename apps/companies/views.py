from rest_framework import generics
from apps.companies.models import Company
from apps.companies.serializers import CompanySerializer


class CompanyCreateListView(generics.ListCreateAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

class CompanyRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
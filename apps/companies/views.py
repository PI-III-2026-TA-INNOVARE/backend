from rest_framework import generics, permissions, response, status, views
from apps.companies.models import Company
from apps.companies.serializers import CompanyCNPJLookupSerializer, CompanySerializer
from apps.companies.services.cnpj_lookup import CNPJNotFoundError, CNPJProviderError, InvalidCNPJError, fetch_cnpj_data

class CompanyCNPJLookupView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CompanyCNPJLookupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payload = fetch_cnpj_data(serializer.validated_data['cnpj'])
        except InvalidCNPJError as exc:
            return response.Response(
                {'code': 'CNPJ_INVALIDO', 'detail': str(exc)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except CNPJNotFoundError as exc:
            return response.Response(
                {'code': 'CNPJ_NAO_ENCONTRADO', 'detail': str(exc)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except CNPJProviderError as exc:
            return response.Response(
                {'code': 'CNPJ_PROVIDER_UNAVAILABLE', 'detail': str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return response.Response(payload, status=status.HTTP_200_OK)

class CompanyCreateListView(generics.ListCreateAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

class CompanyRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
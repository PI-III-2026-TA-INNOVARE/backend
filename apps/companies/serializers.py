from rest_framework import serializers
from apps.companies.models import Company
from apps.companies.services.cnpj_lookup import normalize_cnpj

class CompanySerializer(serializers.ModelSerializer):
    endereco = serializers.SerializerMethodField(read_only=True)
    razao_social = serializers.CharField(source='legal_name', required=False, allow_null=True)
    situacao_cadastral = serializers.CharField(source='registration_status', required=False, allow_null=True)
    municipio = serializers.CharField(source='city', required=False, allow_null=True)
    uf = serializers.CharField(source='state', required=False, allow_null=True)

    class Meta:
        model = Company
        fields = ['id_company','user','cnpj','name','razao_social','situacao_cadastral','municipio','uf','street','number','complement','neighborhood', 'zip_code','endereco','status']

    def get_endereco(self, obj):
        return {
            'logradouro': obj.street,
            'numero': obj.number,
            'complemento': obj.complement,
            'bairro': obj.neighborhood,
            'cep': obj.zip_code,
        }

    def validate_cnpj(self, value):
        return normalize_cnpj(value)

class CompanyCNPJLookupSerializer(serializers.Serializer):
    cnpj = serializers.CharField(max_length=18)

    def validate_cnpj(self, value):
        return normalize_cnpj(value)

class CompanyRegistrationSerializer(serializers.ModelSerializer):
    razao_social = serializers.CharField(source='legal_name')
    situacao_cadastral = serializers.CharField(source='registration_status')
    municipio = serializers.CharField(source='city')
    uf = serializers.CharField(source='state')
    endereco = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ['id_company', 'cnpj', 'razao_social', 'situacao_cadastral', 'municipio', 'uf', 'endereco']

    def get_endereco(self, obj):
        return {
            'logradouro': obj.street,
            'numero': obj.number,
            'complemento': obj.complement,
            'bairro': obj.neighborhood,
            'cep': obj.zip_code,
        }

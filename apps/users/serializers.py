from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from apps.companies.models import Company
from apps.companies.serializers import CompanyRegistrationSerializer
from apps.companies.services.cnpj_lookup import (
    CNPJNotFoundError,
    CNPJProviderError,
    InvalidCNPJError,
    fetch_cnpj_data,
    normalize_cnpj,
)
from apps.research_area.models import ResearchArea
from apps.researchers.models import Researcher
from apps.resumes.models import Resume
from apps.universities.models import University
from apps.users.models import User
from apps.users.services.institutional_domains import (
    InstitutionalDomainsUnavailable,
    is_institutional_email_domain,
)

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    id_tipo = serializers.CharField()

    name = serializers.CharField(required=False, max_length=200)
    status = serializers.BooleanField(required=False, default=True)

    cnpj = serializers.CharField(required=False, max_length=18)

    availability = serializers.BooleanField(required=False, allow_null=True)
    university = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=University.objects.all(),
    )
    resume = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=Resume.objects.all(),
    )
    area = serializers.PrimaryKeyRelatedField(
        required=False,
        many=True,
        queryset=ResearchArea.objects.all(),
    )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este e-mail já está cadastrado.')
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def _normalize_id_tipo(self, value):
        if isinstance(value, int):
            if value == User.UserType.PESQUISADOR:
                return User.UserType.PESQUISADOR
            if value == User.UserType.EMPRESA:
                return User.UserType.EMPRESA
            raise serializers.ValidationError('Tipo inválido. Use 1 (pesquisador) ou 2 (empresa).')

        value = str(value).strip().lower()

        if value in {'1', 'pesquisador'}:
            return User.UserType.PESQUISADOR
        if value in {'2', 'empresa'}:
            return User.UserType.EMPRESA

        raise serializers.ValidationError('Tipo inválido. Use pesquisador/empresa ou 1/2.')

    def validate(self, attrs):
        id_tipo = self._normalize_id_tipo(attrs.get('id_tipo'))
        attrs['id_tipo'] = id_tipo

        if id_tipo == User.UserType.EMPRESA:
            required = ['cnpj']
            missing = [field for field in required if not attrs.get(field)]
            if missing:
                raise serializers.ValidationError({field: 'Este campo é obrigatório.' for field in missing})

            try:
                company_data = fetch_cnpj_data(attrs['cnpj'])
            except InvalidCNPJError as exc:
                raise serializers.ValidationError({'cnpj': str(exc)})
            except CNPJNotFoundError as exc:
                raise serializers.ValidationError({'cnpj': str(exc)})
            except CNPJProviderError:
                raise serializers.ValidationError(
                    {
                        'cnpj': (
                            'Nao foi possivel validar o CNPJ no momento. '
                            'Tente novamente mais tarde.'
                        )
                    }
                )

            if not company_data.get('pode_cadastrar'):
                raise serializers.ValidationError(
                    {
                        'cnpj': (
                            'Nao e possivel cadastrar empresa com situacao cadastral '
                            'diferente de ATIVA.'
                        )
                    }
                )

            attrs['company_official_data'] = company_data
            attrs['cnpj'] = company_data['cnpj']
            cnpj_already_registered = any(
                normalize_cnpj(existing) == company_data['cnpj']
                for existing in Company.objects.values_list('cnpj', flat=True)
            )
            if cnpj_already_registered:
                raise serializers.ValidationError({'cnpj': 'Este CNPJ ja esta cadastrado.'})

        if id_tipo == User.UserType.PESQUISADOR:
            required = ['name']
            missing = [field for field in required if not attrs.get(field)]
            if missing:
                raise serializers.ValidationError({field: 'Este campo é obrigatório.' for field in missing})

            required = ['university']
            missing = [field for field in required if not attrs.get(field)]
            if missing:
                raise serializers.ValidationError({field: 'Este campo é obrigatório.' for field in missing})

            email = attrs.get('email', '')
            email_domain = email.rsplit('@', 1)[-1] if '@' in email else ''
            try:
                is_institutional = is_institutional_email_domain(email_domain)
            except InstitutionalDomainsUnavailable:
                raise serializers.ValidationError(
                    {
                        'email': (
                            'Nao foi possivel validar o dominio institucional no momento. '
                            'Tente novamente mais tarde.'
                        )
                    }
                )

            if not is_institutional:
                raise serializers.ValidationError(
                    {
                        'email': (
                            'Para cadastro de pesquisador, utilize um e-mail institucional valido.'
                        )
                    }
                )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        id_tipo = validated_data.pop('id_tipo')
        password = validated_data.pop('password')
        email = validated_data.pop('email')

        user = User.objects.create_user(
            email=email,
            password=password,
            id_type=id_tipo,
        )

        if id_tipo == User.UserType.EMPRESA:
            company_data = validated_data.pop('company_official_data')
            address = company_data.get('endereco', {})
            company = Company.objects.create(
                user=user,
                name=company_data.get('razao_social'),
                cnpj=company_data['cnpj'],
                registration_status=company_data.get('situacao_cadastral'),
                legal_name=company_data.get('razao_social'),
                city=company_data.get('municipio'),
                state=company_data.get('uf'),
                street=address.get('logradouro'),
                number=address.get('numero'),
                complement=address.get('complemento'),
                neighborhood=address.get('bairro'),
                zip_code=address.get('cep'),
                status=validated_data.get('status', True),
            )
            user._registered_company = company
            return user

        area = validated_data.pop('area', [])
        researcher = Researcher.objects.create(
            user=user,
            name=validated_data['name'],
            availability=validated_data.get('availability'),
            status=validated_data.get('status', True),
            university=validated_data['university'],
            resume=validated_data.get('resume'),
        )
        if area:
            researcher.area.set(area)

        return user


class UserSerializer(serializers.ModelSerializer):
    id_tipo = serializers.IntegerField(source='id_type')
    tipo = serializers.CharField(source='get_id_type_display')

    class Meta:
        model = User
        fields = ['id_user', 'email', 'id_tipo', 'tipo', 'registration_date', 'update_date']


class RegisterResponseSerializer(UserSerializer):
    empresa = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['empresa']

    def get_empresa(self, obj):
        company = getattr(obj, '_registered_company', None)
        if company is None and hasattr(obj, 'company_profile'):
            company = obj.company_profile
        if not company:
            return None
        return CompanyRegistrationSerializer(company).data


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este e-mail não está cadastrado.')
        return value


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'As senhas não coinciden.'})
        return attrs

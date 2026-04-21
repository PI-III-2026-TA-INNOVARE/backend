from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from apps.companies.models import Company
from apps.research_area.models import ResearchArea
from apps.researchers.models import Researcher
from apps.resumes.models import Resume
from apps.universities.models import University
from apps.users.models import User


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    id_tipo = serializers.CharField()

    name = serializers.CharField(required=False, max_length=200)
    status = serializers.BooleanField(required=False, default=True)

    cnpj = serializers.CharField(required=False, max_length=18)
    registration_status = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)

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

        common_required = ['name']
        missing_common = [field for field in common_required if not attrs.get(field)]
        if missing_common:
            raise serializers.ValidationError(
                {field: 'Este campo é obrigatório.' for field in missing_common}
            )

        if id_tipo == User.UserType.EMPRESA:
            required = ['cnpj']
            missing = [field for field in required if not attrs.get(field)]
            if missing:
                raise serializers.ValidationError({field: 'Este campo é obrigatório.' for field in missing})

        if id_tipo == User.UserType.PESQUISADOR:
            required = ['university', 'resume']
            missing = [field for field in required if not attrs.get(field)]
            if missing:
                raise serializers.ValidationError({field: 'Este campo é obrigatório.' for field in missing})

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
            Company.objects.create(
                user=user,
                name=validated_data['name'],
                cnpj=validated_data['cnpj'],
                registration_status=validated_data.get('registration_status'),
                status=validated_data.get('status', True),
            )
            return user

        area = validated_data.pop('area', [])
        researcher = Researcher.objects.create(
            user=user,
            name=validated_data['name'],
            availability=validated_data.get('availability'),
            status=validated_data.get('status', True),
            university=validated_data['university'],
            resume=validated_data['resume'],
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

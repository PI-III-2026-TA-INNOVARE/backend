import secrets
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone

from apps.users.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class UserType(models.IntegerChoices):
        PESQUISADOR = 1, 'pesquisador'
        EMPRESA = 2, 'empresa'

    id_user = models.AutoField(primary_key=True, db_column='id_usuario')
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128, db_column='senha')
    id_type = models.PositiveSmallIntegerField(
        choices=UserType.choices,
        db_column='id_tipo',
        default=UserType.PESQUISADOR,
    )
    registration_date = models.DateTimeField(auto_now_add=True, db_column='dt_cadastro')
    update_date = models.DateTimeField(auto_now=True, db_column='dt_atualizacao')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'usuario'


class PasswordResetToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='password_reset_token')
    token = models.CharField(max_length=255, unique=True, db_column='token_recuperacao')
    created_at = models.DateTimeField(auto_now_add=True, db_column='data_criacao')
    expired_at = models.DateTimeField(db_column='data_expiracao')

    class Meta:
        db_table = 'password_reset_token'

    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)

    def is_valid(self):
        return timezone.now() < self.expired_at

    @classmethod
    def create_for_user(cls, user, expires_in_hours=24):
        token = cls.generate_token()
        expired_at = timezone.now() + timedelta(hours=expires_in_hours)
        reset_token, created = cls.objects.update_or_create(
            user=user,
            defaults={'token': token, 'expired_at': expired_at}
        )
        return reset_token

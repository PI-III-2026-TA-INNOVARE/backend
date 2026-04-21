from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

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

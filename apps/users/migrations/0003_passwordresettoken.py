import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_user_groups_alter_user_is_superuser_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PasswordResetToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(db_column='token_recuperacao', max_length=255, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='data_criacao')),
                ('expired_at', models.DateTimeField(db_column='data_expiracao')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='password_reset_token', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'password_reset_token',
            },
        ),
    ]

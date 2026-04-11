from django.db import models
from apps.resumes.models import Resume

class Experience(models.Model):
    id_experience = models.AutoField(primary_key=True, db_column='id_experiencia')
    description = models.TextField(db_column='descricao')
    start_date = models.DateField(db_column='dt_inicio')
    end_date = models.DateField(null=True, blank=True, db_column='dt_termino')
    resume = models.ForeignKey(Resume, on_delete=models.PROTECT, related_name='experience', db_column='id_curriculo')

    def __str__(self):
        return self.description

    class Meta:
        db_table = 'experiencia'
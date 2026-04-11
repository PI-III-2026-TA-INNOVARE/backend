from django.db import models
from apps.resumes.models import Resume

class Education(models.Model):
    id_education = models.AutoField(primary_key=True, db_column='id_formacao')
    course = models.CharField(max_length=200, db_column='curso')
    institution = models.CharField(max_length=200, db_column='instituicao')
    start_date = models.DateField(db_column='dt_inicio')
    end_date = models.DateField(db_column='dt_termino')
    resume = models.ForeignKey(Resume, on_delete=models.PROTECT, related_name='education', db_column='id_curriculo')

    def __str__(self):
        return self.course

    class Meta:
        db_table = 'formacao'
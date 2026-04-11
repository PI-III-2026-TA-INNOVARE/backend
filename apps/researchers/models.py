from django.db import models
from apps.universities.models import University
from apps.resumes.models import Resume

class Researcher(models.Model):
    id_researcher = models.AutoField(primary_key=True, db_column='id_pesquisador')
    name = models.CharField(max_length=200, db_column='nome')
    availability = models.BooleanField(blank=True, null=True, db_column='disponibilidade')
    status = models.BooleanField(default=True)
    university = models.ForeignKey(University, on_delete=models.PROTECT, related_name='researcher', db_column='id_universidade')
    resume = models.OneToOneField(Resume, on_delete=models.PROTECT, related_name='researcher', db_column='id_curriculo')

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'pesquisador'

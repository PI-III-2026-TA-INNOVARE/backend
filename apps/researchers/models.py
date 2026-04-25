from django.db import models
from django.conf import settings
from apps.universities.models import University
from apps.resumes.models import Resume
from apps.research_area.models import ResearchArea

class Researcher(models.Model):
    id_researcher = models.AutoField(primary_key=True, db_column='id_pesquisador')
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='researcher_profile',
        db_column='id_usuario',
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=200, db_column='nome')
    availability = models.BooleanField(blank=True, null=True, db_column='disponibilidade')
    status = models.BooleanField(default=True)
    university = models.ForeignKey(University, on_delete=models.PROTECT, related_name='researcher', db_column='id_universidade')
    resume = models.OneToOneField(Resume, on_delete=models.PROTECT, related_name='researcher', db_column='id_curriculo', blank=True, null=True)
    area = models.ManyToManyField(ResearchArea, related_name='researcher')
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'pesquisador'

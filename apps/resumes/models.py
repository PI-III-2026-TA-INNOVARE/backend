from django.db import models
from apps.skills.models import Skill

class Resume(models.Model):
    id_resume = models.AutoField(primary_key=True, db_column='id_curriculo')
    skill = models.ManyToManyField(Skill, related_name='resume')

    def __str__(self):
        return str(self.id_resume)

    class Meta:
        db_table = 'curriculo'
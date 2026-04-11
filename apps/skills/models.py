from django.db import models

class Skill(models.Model):
    id_skill = models.AutoField(primary_key=True, db_column='id_habilidade')
    description = models.CharField(max_length=255, db_column='descricao')

    def __str__(self):
        return self.description

    class Meta:
        db_table = 'habilidade'
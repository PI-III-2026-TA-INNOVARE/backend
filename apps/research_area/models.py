from django.db import models

class ResearchArea(models.Model):
    id_area = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, db_column='nome')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'area_pesquisa'
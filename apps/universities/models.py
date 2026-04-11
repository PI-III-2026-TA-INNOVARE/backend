from django.db import models

class University(models.Model):
    id_university = models.AutoField(primary_key=True, db_column='id_universidade')
    name = models.CharField(max_length=255, db_column='nome')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'universidade'
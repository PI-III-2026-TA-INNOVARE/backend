from django.db import models
from apps.companies.models import Company
from apps.researchers.models import Researcher
from apps.research_area.models import ResearchArea

class Research(models.Model):
    id_research = models.AutoField(primary_key=True, db_column='id_pesquisa')
    title = models.CharField(max_length=200, db_column='titulo')
    status = models.CharField(max_length=20, default='pendente')
    scope = models.TextField(db_column='escopo')
    goal = models.TextField(db_column='objetivo')
    justification = models.TextField(db_column='justificativa')
    results = models.TextField(db_column='resultados')
    deadline = models.DateTimeField(db_column='prazo')
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='research', db_column='id_empresa')
    researcher = models.ForeignKey(Researcher, on_delete=models.PROTECT, related_name='research', db_column='id_universidade', blank=True, null=True,)
    area = models.ForeignKey(ResearchArea, on_delete=models.PROTECT, related_name='research', db_column='id_area')
    registration_date = models.DateTimeField(auto_now_add=True, db_column='dt_cadastro')
    update_date = models.DateTimeField(auto_now=True, db_column='dt_atualizacao')

    def __str__(self):
        return self.title
    
    class Meta:
        db_table = 'pesquisa'
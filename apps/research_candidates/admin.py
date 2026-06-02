from django.contrib import admin
from .models import ResearchCandidate, Notification

@admin.register(ResearchCandidate)
class ResearchCandidateAdmin(admin.ModelAdmin):
    list_display = ('id_candidate', 'research', 'researcher', 'source', 'status', 'score_match', 'created_at')
    list_filter = ('source', 'status')
    search_fields = ('research__title', 'researcher__name')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'tipo', 'titulo', 'lido', 'data_criacao')
    list_filter = ('tipo', 'lido')
    search_fields = ('user__username', 'titulo', 'mensagem')

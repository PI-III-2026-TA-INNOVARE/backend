from django.contrib import admin
from .models import ResearchCandidate

@admin.register(ResearchCandidate)
class ResearchCandidateAdmin(admin.ModelAdmin):
    list_display = ('id_candidate', 'research', 'researcher', 'source', 'status', 'score_match', 'created_at')
    list_filter = ('source', 'status')
    search_fields = ('research__title', 'researcher__name')

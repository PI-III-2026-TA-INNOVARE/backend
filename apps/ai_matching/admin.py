from django.contrib import admin
from .models import MatchingProfile, Match, MatchingHistory


@admin.register(MatchingProfile)
class MatchingProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'profile_type', 'is_active', 'created_at']
    list_filter = ['profile_type', 'is_active', 'created_at']
    search_fields = ['user__username', 'description', 'keywords']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'profile_type', 'is_active')
        }),
        ('Perfil', {
            'fields': ('researcher', 'company')
        }),
        ('Detalhes', {
            'fields': ('description', 'keywords')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = [
        'researcher',
        'company',
        'compatibility_score',
        'status',
        'created_at'
    ]
    list_filter = ['status', 'compatibility_score', 'created_at']
    search_fields = ['researcher__name', 'company__legal_name', 'company__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Matching', {
            'fields': ('researcher', 'company', 'compatibility_score', 'status')
        }),
        ('Análise IA', {
            'fields': ('match_reason', 'ai_analysis', 'search_query')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MatchingHistory)
class MatchingHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'query_type', 'results_count', 'created_at']
    list_filter = ['query_type', 'created_at']
    search_fields = ['user__username', 'search_query']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Busca', {
            'fields': ('user', 'search_query', 'query_type')
        }),
        ('Resultados', {
            'fields': ('results_count', 'ai_response')
        }),
        ('Data', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

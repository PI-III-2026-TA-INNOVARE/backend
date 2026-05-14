from django.urls import path

from apps.search.views import SearchReindexView, SearchResearchView, SearchResearchersView


urlpatterns = [
    path('search/researchers/', SearchResearchersView.as_view(), name='search-researchers'),
    path('search/research/', SearchResearchView.as_view(), name='search-research'),
    path('search/reindex/', SearchReindexView.as_view(), name='search-reindex'),
]

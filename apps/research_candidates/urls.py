from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PropostaViewSet,
    ResearchCandidateStatusUpdateView,
    ResearchCandidatesListView,
    ResearchInterestCreateView,
    ResearchMatchRunView,
    ResearchMyInterestsView,
    ResearchMyRecommendationAcceptView,
    ResearchMyRecommendationRejectView,
    ResearchMySuggestionsView,
    ResearchMySuggestionAcceptView,
    ResearchMySuggestionRejectView,
    ResearcherRecommendationsView,
)

router = DefaultRouter()
router.register(r'propostas', PropostaViewSet, basename='proposta')

urlpatterns = [
    path('', include(router.urls)),
    path('research/my-interests/', ResearchMyInterestsView.as_view(), name='research-my-interests'),
    path('research/my-suggestions/', ResearchMySuggestionsView.as_view(), name='research-my-suggestions'),
    path('research/my-recommendations/', ResearcherRecommendationsView.as_view(), name='research-my-recommendations'),
    path('research/my-recommendations/<int:candidate_id>/accept/', ResearchMyRecommendationAcceptView.as_view(), name='research-my-recommendation-accept'),
    path('research/my-recommendations/<int:candidate_id>/reject/', ResearchMyRecommendationRejectView.as_view(), name='research-my-recommendation-reject'),
    path('research/my-suggestions/<int:candidate_id>/accept/', ResearchMySuggestionAcceptView.as_view(), name='research-my-suggestion-accept'),
    path('research/my-suggestions/<int:candidate_id>/reject/', ResearchMySuggestionRejectView.as_view(), name='research-my-suggestion-reject'),
    path('research/<int:pk>/candidates/', ResearchCandidatesListView.as_view(), name='research-candidates-list'),
    path('research/<int:pk>/candidates/<int:candidate_id>/', ResearchCandidateStatusUpdateView.as_view(), name='research-candidate-status-update'),
    path('research/<int:pk>/interest/', ResearchInterestCreateView.as_view(), name='research-interest-create'),
    path('research/<int:pk>/match/run/', ResearchMatchRunView.as_view(), name='research-match-run'),
]

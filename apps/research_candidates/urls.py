from django.urls import path
from .views import (
    ResearchCandidatesListView,
    ResearchCandidateStatusUpdateView,
    ResearchInterestCreateView,
    ResearchMatchRunView,
    ResearchMyInterestsView,
    ResearchMySuggestionAcceptView,
    ResearchMySuggestionRejectView,
    ResearchMySuggestionsView,
    ResearchMyRecommendationAcceptView,
    ResearchMyRecommendationRejectView,
    ResearcherRecommendationsView,
)

urlpatterns = [
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

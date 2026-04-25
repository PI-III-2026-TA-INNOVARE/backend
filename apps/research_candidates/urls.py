from django.urls import path
from .views import ResearchCandidatesListView, ResearchCandidateStatusUpdateView, ResearchInterestCreateView, ResearchMatchRunView, ResearchMyInterestsView

urlpatterns = [
    path('research/my-interests/', ResearchMyInterestsView.as_view(), name='research-my-interests'),
    path('research/<int:pk>/candidates/', ResearchCandidatesListView.as_view(), name='research-candidates-list'),
    path('research/<int:pk>/candidates/<int:candidate_id>/', ResearchCandidateStatusUpdateView.as_view(), name='research-candidate-status-update'),
    path('research/<int:pk>/interest/', ResearchInterestCreateView.as_view(), name='research-interest-create'),
    path('research/<int:pk>/match/run/', ResearchMatchRunView.as_view(), name='research-match-run'),
]

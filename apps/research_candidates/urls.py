from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResearchCandidatesListView, ResearchCandidateStatusUpdateView, ResearchInterestCreateView, ResearchMatchRunView, ResearchMyInterestsView, NotificationViewSet

router = DefaultRouter()
router.register(r'notificacoes', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('research/my-interests/', ResearchMyInterestsView.as_view(), name='research-my-interests'),
    path('research/<int:pk>/candidates/', ResearchCandidatesListView.as_view(), name='research-candidates-list'),
    path('research/<int:pk>/candidates/<int:candidate_id>/', ResearchCandidateStatusUpdateView.as_view(), name='research-candidate-status-update'),
    path('research/<int:pk>/interest/', ResearchInterestCreateView.as_view(), name='research-interest-create'),
    path('research/<int:pk>/match/run/', ResearchMatchRunView.as_view(), name='research-match-run'),
]

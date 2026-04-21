from django.urls import path
from .views import ResearchCreateListView, ResearchRetrieveUpdateDestroy

urlpatterns = [
    path('research/', ResearchCreateListView.as_view(), name='research-create-list'),
    path('research/<int:pk>', ResearchRetrieveUpdateDestroy.as_view(), name='research-detail-view'),
]
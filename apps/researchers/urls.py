from django.urls import path
from .views import ResearcherCreateListView, ResearcherRetrieveUpdateDestroy

urlpatterns = [
    path('researchers/', ResearcherCreateListView.as_view(), name='researcher-create-list'),
    path('researchers/<int:pk>', ResearcherRetrieveUpdateDestroy.as_view(), name='researcher-detail-view'),
]
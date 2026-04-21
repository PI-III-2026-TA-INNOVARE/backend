from django.urls import path
from .views import ResearchAreaCreateListView, ResearchAreaRetrieveUpdateDestroy

urlpatterns = [
    path('research/area/', ResearchAreaCreateListView.as_view(), name='area-create-list'),
    path('research/area/<int:pk>', ResearchAreaRetrieveUpdateDestroy.as_view(), name='area-detail-view'),
]
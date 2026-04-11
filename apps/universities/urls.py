from django.urls import path
from .views import UniversityCreateListView, UniversityRetrieveUpdateDestroy

urlpatterns = [
    path('universities/', UniversityCreateListView.as_view(), name='universities-create-list'),
    path('universities/<int:pk>', UniversityRetrieveUpdateDestroy.as_view(), name='universities-detail-view'),
]
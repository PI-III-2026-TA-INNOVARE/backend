from django.urls import path
from .views import ExperienceCreateListView, ExperienceRetrieveUpdateDestroy

urlpatterns = [
    path('experiences/', ExperienceCreateListView.as_view(), name='experience-create-list'),
    path('experiences/<int:pk>', ExperienceRetrieveUpdateDestroy.as_view(), name='experience-detail-view'),
]
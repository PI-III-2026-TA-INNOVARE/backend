from django.urls import path
from .views import EducationCreateListView, EducationRetrieveUpdateDestroy

urlpatterns = [
    path('educations/', EducationCreateListView.as_view(), name='education-create-list'),
    path('educations/<int:pk>', EducationRetrieveUpdateDestroy.as_view(), name='education-detail-view'),
]
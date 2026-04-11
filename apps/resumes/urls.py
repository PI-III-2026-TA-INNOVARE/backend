from django.urls import path
from .views import ResumeCreateListView, ResumeRetrieveUpdateDestroy, ResearcherResumeView

urlpatterns = [
    path('resumes/', ResumeCreateListView.as_view(), name='resume-create-list'),
    path('resumes/<int:pk>', ResumeRetrieveUpdateDestroy.as_view(), name='resume-detail-view'),
    path('researchers/<int:pk>/resume/', ResearcherResumeView.as_view()),
]
from django.urls import path
from .views import CompanyDashboardView, ResearcherDashboardView

urlpatterns = [
    path('dashboard/researcher/', ResearcherDashboardView.as_view(), name='research-dashboard-researcher'),
    path('dashboard/company/', CompanyDashboardView.as_view(), name='research-dashboard-company'),
]

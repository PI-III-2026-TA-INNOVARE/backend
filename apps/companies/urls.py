from django.urls import path
from .views import CompanyCreateListView, CompanyRetrieveUpdateDestroy

urlpatterns = [
    path('companies/', CompanyCreateListView.as_view(), name='company-create-list'),
    path('companies/<int:pk>', CompanyRetrieveUpdateDestroy.as_view(), name='company-detail-view'),
]
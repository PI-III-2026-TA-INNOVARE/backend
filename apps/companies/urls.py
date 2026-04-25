from django.urls import path
from .views import CompanyCNPJLookupView, CompanyCreateListView, CompanyRetrieveUpdateDestroy

urlpatterns = [
    path('companies/cnpj-lookup/', CompanyCNPJLookupView.as_view(), name='company-cnpj-lookup'),
    path('companies/', CompanyCreateListView.as_view(), name='company-create-list'),
    path('companies/<int:pk>', CompanyRetrieveUpdateDestroy.as_view(), name='company-detail-view'),
]
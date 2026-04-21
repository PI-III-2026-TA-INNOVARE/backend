from django.urls import path

from apps.users.views import LoginView, ProfileView, RefreshView, RegisterView


urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/token/', LoginView.as_view(), name='token-obtain-pair'),
    path('auth/token/refresh/', RefreshView.as_view(), name='token-refresh'),
    path('auth/profile/', ProfileView.as_view(), name='auth-profile'),
]

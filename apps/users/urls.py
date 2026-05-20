from django.urls import path

from apps.users.views import (
    LoginView, ProfileView, RefreshView, RegisterView,
    ForgotPasswordView, ResetPasswordView
)


urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/token/', LoginView.as_view(), name='token-obtain-pair'),
    path('auth/token/refresh/', RefreshView.as_view(), name='token-refresh'),
    path('auth/profile/', ProfileView.as_view(), name='auth-profile'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='auth-forgot-password'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='auth-reset-password'),
]

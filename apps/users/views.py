from rest_framework import generics, permissions, response, status, views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.companies.serializers import CompanyRegistrationSerializer
from apps.researchers.serializers import ResearcherSerializer
from apps.users.models import User, PasswordResetToken
from apps.users.serializers import (
    RegisterResponseSerializer, RegisterSerializer, UserSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer
)
from apps.users.services.email import send_password_reset_email


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return response.Response(RegisterResponseSerializer(user).data, status=status.HTTP_201_CREATED)


class ProfileView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        payload = UserSerializer(user).data

        if user.id_type == User.UserType.EMPRESA and hasattr(user, 'company_profile'):
            payload['empresa'] = CompanyRegistrationSerializer(user.company_profile).data

        if user.id_type == User.UserType.PESQUISADOR and hasattr(user, 'researcher_profile'):
            payload['pesquisador'] = ResearcherSerializer(user.researcher_profile).data

        return response.Response(payload, status=status.HTTP_200_OK)


class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]


class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class ForgotPasswordView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        reset_token = PasswordResetToken.create_for_user(user)

        try:
            send_password_reset_email(
                user_email=user.email,
                reset_token=reset_token,
                frontend_url=request.data.get('frontend_url')
            )
        except Exception as e:
            print(f"ERRO AO ENVIAR EMAIL: {str(e)}")
            import traceback
            traceback.print_exc()
            return response.Response(
                {'detail': f'Erro ao enviar e-mail: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return response.Response(
            {'detail': 'Link de redefinição de senha enviado para o e-mail.'},
            status=status.HTTP_200_OK
        )


class ResetPasswordView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_str = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            reset_token = PasswordResetToken.objects.get(token=token_str)
        except PasswordResetToken.DoesNotExist:
            return response.Response(
                {'detail': 'Token inválido.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not reset_token.is_valid():
            return response.Response(
                {'detail': 'Token expirado. Solicit um novo link de redefinição.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = reset_token.user
        user.set_password(new_password)
        user.save()

        reset_token.delete()

        return response.Response(
            {'detail': 'Senha redefinida com sucesso.'},
            status=status.HTTP_200_OK
        )

from rest_framework import generics, permissions, response, status, views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.companies.serializers import CompanySerializer
from apps.researchers.serializers import ResearcherSerializer
from apps.users.models import User
from apps.users.serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return response.Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class ProfileView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        payload = UserSerializer(user).data

        if user.id_type == User.UserType.EMPRESA and hasattr(user, 'company_profile'):
            payload['empresa'] = CompanySerializer(user.company_profile).data

        if user.id_type == User.UserType.PESQUISADOR and hasattr(user, 'researcher_profile'):
            payload['pesquisador'] = ResearcherSerializer(user.researcher_profile).data

        return response.Response(payload, status=status.HTTP_200_OK)


class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]


class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]

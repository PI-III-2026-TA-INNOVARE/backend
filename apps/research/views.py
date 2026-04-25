from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from apps.research.models import Research
from apps.research.serializers import ResearchSerializer
from apps.users.models import User

class IsCompanyForCreate(permissions.BasePermission):
    message = 'Apenas usuários do tipo empresa podem criar pesquisas.'

    def has_permission(self, request, view):
        if request.method != 'POST':
            return True

        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.id_type == User.UserType.EMPRESA
            and hasattr(user, 'company_profile')
        )

class IsCompanyOwnerForMutation(permissions.BasePermission):
    message = 'Somente a empresa dona da pesquisa pode alterar este recurso.'

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        return bool(user and user.is_authenticated and user.id_type == User.UserType.EMPRESA and hasattr(user, 'company_profile') and obj.company_id == user.company_profile.id_company)

class ResearchCreateListView(generics.ListCreateAPIView):
    queryset = Research.objects.select_related('company', 'area').all()
    serializer_class = ResearchSerializer
    permission_classes = [permissions.IsAuthenticated, IsCompanyForCreate]

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied('Autenticacao obrigatoria.')
        if user.id_type != User.UserType.EMPRESA:
            raise PermissionDenied('Apenas usuários do tipo empresa podem criar pesquisas.')
        if not hasattr(user, 'company_profile'):
            raise PermissionDenied('Usuário empresa sem perfil de empresa vinculado.')

        serializer.save(company=user.company_profile)

class ResearchRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Research.objects.select_related('company', 'area').all()
    serializer_class = ResearchSerializer
    permission_classes = [permissions.IsAuthenticated, IsCompanyOwnerForMutation]
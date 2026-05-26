from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.research_candidates.models import ResearchCandidate
from .serializers import PropostaSerializer

class PropostaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar propostas (ResearchCandidate com source='manual').
    
    Endpoints:
    - GET /api/propostas/ - Listar todas as propostas
    - POST /api/propostas/ - Criar nova proposta
    - GET /api/propostas/{id}/ - Detalhes da proposta
    - PUT/PATCH /api/propostas/{id}/ - Atualizar proposta
    - DELETE /api/propostas/{id}/ - Deletar proposta
    """
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PropostaSerializer

    def get_queryset(self):
        # Retorna apenas propostas (source='manual')
        return ResearchCandidate.objects.filter(source='manual')

    def create(self, request, *args, **kwargs):
        """Criar uma nova proposta setando source='manual'"""
        data = request.data.copy()
        data['source'] = 'manual'
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'])
    def minhas_propostas(self, request):
        """Retorna propostas do pesquisador autenticado"""
        propostas = self.get_queryset().filter(researcher__user=request.user)
        serializer = self.get_serializer(propostas, many=True)
        return Response(serializer.data)

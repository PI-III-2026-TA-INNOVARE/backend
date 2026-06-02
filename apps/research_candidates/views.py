from decimal import Decimal
from uuid import uuid4
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, response, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from apps.research.models import Research
from apps.researchers.models import Researcher
from .models import ResearchCandidate, Notification
from .serializers import (
    ResearchCandidateSerializer, 
    ResearchCandidateStatusUpdateSerializer, 
    ResearchInterestSerializer, 
    ResearchMatchRunResponseSerializer, 
    ResearcherInterestListSerializer, 
    NotificationSerializer
)
from apps.users.models import User

class _ResearchCompanyOwnerMixin:
    def get_research(self):
        research = get_object_or_404(Research.objects.select_related('company'), pk=self.kwargs['pk'])
        user = self.request.user
        if not (
            user.is_authenticated
            and user.id_type == User.UserType.EMPRESA
            and hasattr(user, 'company_profile')
            and research.company_id == user.company_profile.id_company
        ):
            raise PermissionDenied('Somente a empresa dona da pesquisa pode acessar candidatos.')
        return research

class ResearchCandidatesListView(_ResearchCompanyOwnerMixin, generics.ListAPIView):
    serializer_class = ResearchCandidateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        research = self.get_research()
        queryset = ResearchCandidate.objects.select_related('researcher').filter(research=research)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        source_filter = self.request.query_params.get('source')
        if source_filter:
            queryset = queryset.filter(source=source_filter)

        ordering = self.request.query_params.get('ordering', '-score_match')
        allowed_ordering = {'-score_match', 'score_match', '-created_at', 'created_at'}
        if ordering not in allowed_ordering:
            ordering = '-score_match'
        return queryset.order_by(ordering, '-id_candidate')

class ResearchCandidateStatusUpdateView(_ResearchCompanyOwnerMixin, generics.UpdateAPIView):
    serializer_class = ResearchCandidateStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        research = self.get_research()
        return get_object_or_404(
            ResearchCandidate.objects.filter(research=research),
            pk=self.kwargs['candidate_id'],
        )


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para notificações do usuário autenticado"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Retorna apenas notificações do usuário autenticado"""
        return Notification.objects.filter(user=self.request.user).order_by('-data_criacao')

    @action(detail=True, methods=['post'])
    def marcar_como_lido(self, request, pk=None):
        """Marca uma notificação como lida"""
        notificacao = self.get_object()
        notificacao.lido = True
        notificacao.data_leitura = timezone.now()
        notificacao.save()
        return response.Response(
            {'status': 'Notificação marcada como lida'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'])
    def marcar_todas_como_lidas(self, request):
        """Marca todas as notificações como lidas"""
        notificacoes = self.get_queryset().filter(lido=False)
        agora = timezone.now()
        notificacoes.update(lido=True, data_leitura=agora)
        return response.Response(
            {'status': f'{notificacoes.count()} notificações marcadas como lidas'},
            status=status.HTTP_200_OK
        )

class ResearchInterestCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        if user.id_type != User.UserType.PESQUISADOR or not hasattr(user, 'researcher_profile'):
            raise PermissionDenied('Apenas usuários do tipo pesquisador podem demonstrar interesse.')

        research = get_object_or_404(Research, pk=pk)
        payload = ResearchInterestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        researcher = user.researcher_profile
        message = payload.validated_data.get('interest_message')

        with transaction.atomic():
            candidate, created = ResearchCandidate.objects.get_or_create(
                research=research,
                researcher=researcher,
                defaults={
                    'source': ResearchCandidate.Source.INTEREST,
                    'status': ResearchCandidate.CandidateStatus.INTERESTED,
                    'interest_message': message,
                },
            )

            if not created:
                candidate.source = ResearchCandidate.Source.INTEREST
                candidate.status = ResearchCandidate.CandidateStatus.INTERESTED
                if message is not None:
                    candidate.interest_message = message
                candidate.save(update_fields=['source', 'status', 'interest_message', 'updated_at'])

        serializer = ResearchCandidateSerializer(candidate)
        return response.Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

class ResearchMyInterestsView(generics.ListAPIView):
    serializer_class = ResearcherInterestListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.id_type != User.UserType.PESQUISADOR or not hasattr(user, 'researcher_profile'):
            raise PermissionDenied('Apenas usuarios pesquisador podem acessar seus interesses.')

        return (
            ResearchCandidate.objects.select_related('research')
            .filter(researcher=user.researcher_profile)
            .order_by('-updated_at')
        )

class ResearchMatchRunView(_ResearchCompanyOwnerMixin, views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        research = self.get_research()
        # In actual implementation this should trigger the celery task
        from .tasks import run_match_for_research_task
        run_match_for_research_task.delay(research.id_research)
        
        return response.Response(
            {'status': 'Matching process started in background'},
            status=status.HTTP_202_ACCEPTED
        )

from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, response, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from apps.research.models import Research
from apps.researchers.models import Researcher
from .models import ResearchCandidate
from .serializers import (
    ResearchCandidateSerializer, 
    ResearchCandidateCreateSerializer,
    ResearchCandidateStatusUpdateSerializer, 
    ResearchInterestSerializer, 
    ResearchMatchRunResponseSerializer, 
    ResearcherInterestListSerializer,
    PropostaSerializer
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

class ResearchCandidatesListView(_ResearchCompanyOwnerMixin, generics.ListCreateAPIView):
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

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ResearchCandidateCreateSerializer
        return ResearchCandidateSerializer

    def create(self, request, *args, **kwargs):
        research = self.get_research()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            candidate, created = ResearchCandidate.objects.get_or_create(
                research=research,
                researcher=serializer.validated_data['researcher'],
                defaults={
                    'source': ResearchCandidate.Source.MANUAL,
                    'status': ResearchCandidate.CandidateStatus.UNDER_REVIEW,
                },
            )

            updated_fields = []
            if candidate.source != ResearchCandidate.Source.MANUAL:
                candidate.source = ResearchCandidate.Source.MANUAL
                updated_fields.append('source')

            if candidate.status in {
                ResearchCandidate.CandidateStatus.SUGGESTED,
                ResearchCandidate.CandidateStatus.INTERESTED,
            }:
                candidate.status = ResearchCandidate.CandidateStatus.UNDER_REVIEW
                updated_fields.append('status')

            if updated_fields and not created:
                updated_fields.append('updated_at')
                candidate.save(update_fields=updated_fields)

        output = ResearchCandidateSerializer(candidate)
        return response.Response(
            output.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

class ResearchCandidateStatusUpdateView(_ResearchCompanyOwnerMixin, generics.UpdateAPIView):
    serializer_class = ResearchCandidateStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        research = self.get_research()
        return get_object_or_404(
            ResearchCandidate.objects.filter(research=research),
            pk=self.kwargs['candidate_id'],
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
            .filter(
                researcher=user.researcher_profile,
                source=ResearchCandidate.Source.INTEREST,
            )
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

class PropostaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar propostas (ResearchCandidate com source='manual').
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

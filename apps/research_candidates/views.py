from decimal import Decimal
from uuid import uuid4
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, response, status, views
from rest_framework.exceptions import PermissionDenied
from apps.research.models import Research, Researcher
from .models import ResearchCandidate
from .serializers import ResearchCandidateSerializer, ResearchCandidateStatusUpdateSerializer, ResearchInterestSerializer, ResearchMatchRunResponseSerializer, ResearcherInterestListSerializer
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
    http_method_names = ['patch']

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
            .filter(researcher=user.researcher_profile)
            .order_by('-updated_at')
        )

class ResearchMatchRunView(_ResearchCompanyOwnerMixin, views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        research = self.get_research()
        job_id = uuid4()

        # Placeholder de matching: candidatos ativos/disponiveis da mesma area da pesquisa.
        potential_researchers = (
            Researcher.objects.filter(status=True, availability=True, area=research.area)
            .distinct()
            .order_by('id_researcher')[:100]
        )

        for researcher in potential_researchers:
            candidate, created = ResearchCandidate.objects.get_or_create(
                research=research,
                researcher=researcher,
                defaults={
                    'source': ResearchCandidate.Source.AI,
                    'status': ResearchCandidate.CandidateStatus.SUGGESTED,
                    'score_match': Decimal('1.0000'),
                    'ai_run_id': job_id,
                },
            )
            if created:
                continue

            # Nao sobrescreve fluxos manuais/interesse ja existentes.
            if candidate.source in {ResearchCandidate.Source.INTEREST, ResearchCandidate.Source.MANUAL}:
                continue

            candidate.source = ResearchCandidate.Source.AI
            if candidate.status == ResearchCandidate.CandidateStatus.SUGGESTED:
                candidate.score_match = Decimal('1.0000')
            candidate.ai_run_id = job_id
            candidate.save(update_fields=['source', 'score_match', 'ai_run_id', 'updated_at'])

        payload = {'research_id': research.id_research, 'job_id': job_id, 'status': 'queued'}
        serializer = ResearchMatchRunResponseSerializer(payload)
        return response.Response(serializer.data, status=status.HTTP_202_ACCEPTED)
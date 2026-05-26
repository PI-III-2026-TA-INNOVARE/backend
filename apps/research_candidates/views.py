from decimal import Decimal

from django.conf import settings
from django.db.models import Q
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, response, status, views
from rest_framework.exceptions import PermissionDenied
from apps.research.models import Research
from .models import ResearchCandidate
from .serializers import ResearchCandidateSerializer, ResearchCandidateStatusUpdateSerializer, ResearchInterestSerializer, ResearchMatchRunResponseSerializer, ResearcherInterestListSerializer, ResearcherRecommendationListSerializer
from .services import run_match_for_research, run_match_for_researcher
from .tasks import run_match_for_research_task
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


class ResearcherRecommendationsView(generics.ListAPIView):
    serializer_class = ResearcherRecommendationListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.id_type != User.UserType.PESQUISADOR or not hasattr(user, 'researcher_profile'):
            raise PermissionDenied('Apenas usuarios pesquisador podem acessar recomendacoes.')

        refresh = self.request.query_params.get('refresh')
        if str(refresh).strip().lower() in {'1', 'true', 'sim', 'yes'}:
            run_match_for_researcher(user.researcher_profile.id_researcher)

        min_score = Decimal(
            str(getattr(settings, 'AI_MATCH_RECOMMENDATION_MIN_SCORE', getattr(settings, 'AI_MATCH_MIN_SCORE', 0.30)))
        )
        strong_reason_filter = (
            Q(match_reasons__contains=['alta_similaridade_semantica'])
            | Q(match_reasons__contains=['similaridade_semantica_moderada'])
            | Q(match_reasons__contains=['boa_aderencia_textual'])
            | Q(match_reasons__contains=['mesma_area_de_pesquisa'])
        )

        return (
            ResearchCandidate.objects.select_related('research', 'research__area', 'research__company')
            .filter(
                researcher=user.researcher_profile,
                source=ResearchCandidate.Source.AI,
                score_match__gte=min_score,
            )
            .filter(strong_reason_filter)
            .order_by('-score_match', '-updated_at')
        )

class ResearchMatchRunView(_ResearchCompanyOwnerMixin, views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        research = self.get_research()
        if getattr(settings, 'AI_MATCH_ASYNC_ENABLED', False):
            task = run_match_for_research_task.delay(research.id_research)
            payload = {
                'research_id': research.id_research,
                'job_id': task.id,
                'status': 'queued',
                'updated': 0,
                'removed': 0,
            }
            serializer = ResearchMatchRunResponseSerializer(payload)
            return response.Response(serializer.data, status=status.HTTP_202_ACCEPTED)

        result = run_match_for_research(research.id_research)
        payload = {
            'research_id': research.id_research,
            'job_id': result.get('run_id'),
            'status': 'done' if result.get('ok') else 'error',
            'updated': result.get('updated', 0),
            'removed': result.get('removed', 0),
        }
        serializer = ResearchMatchRunResponseSerializer(payload)
        return response.Response(serializer.data, status=status.HTTP_200_OK if result.get('ok') else status.HTTP_400_BAD_REQUEST)

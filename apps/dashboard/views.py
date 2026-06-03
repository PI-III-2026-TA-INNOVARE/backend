from apps.research_candidates.models import ResearchCandidate
from apps.research.models import Research
from django.db.models import Avg, Count, Q
from rest_framework import permissions, response, status, views
from rest_framework.exceptions import PermissionDenied, ValidationError
from apps.users.models import User
from django.shortcuts import get_object_or_404


def _parse_optional_int(raw_value, field_name):
    if raw_value in (None, ''):
        return None
    try:
        return int(raw_value)
    except ValueError:
        raise ValidationError({field_name: f'{field_name} deve ser numero inteiro.'})


def _float_or_none(value):
    return None if value is None else float(value)


def _candidate_breakdown_summary(queryset):
    return queryset.aggregate(
        total_candidates=Count('id_candidate'),
        average_score=Avg('score_match'),
        ai_suggested_candidates=Count(
            'id_candidate',
            filter=Q(source=ResearchCandidate.Source.AI, status=ResearchCandidate.CandidateStatus.SUGGESTED),
        ),
        ai_interested_candidates=Count(
            'id_candidate',
            filter=Q(source=ResearchCandidate.Source.AI, status=ResearchCandidate.CandidateStatus.INTERESTED),
        ),
        ai_under_review_candidates=Count(
            'id_candidate',
            filter=Q(source=ResearchCandidate.Source.AI, status=ResearchCandidate.CandidateStatus.UNDER_REVIEW),
        ),
        ai_approved_candidates=Count(
            'id_candidate',
            filter=Q(source=ResearchCandidate.Source.AI, status=ResearchCandidate.CandidateStatus.APPROVED),
        ),
        ai_rejected_candidates=Count(
            'id_candidate',
            filter=Q(source=ResearchCandidate.Source.AI, status=ResearchCandidate.CandidateStatus.REJECTED),
        ),
        manual_suggested_candidates=Count(
            'id_candidate',
            filter=Q(source=ResearchCandidate.Source.MANUAL, status=ResearchCandidate.CandidateStatus.SUGGESTED),
        ),
        manual_interested_candidates=Count(
            'id_candidate',
            filter=Q(source=ResearchCandidate.Source.MANUAL, status=ResearchCandidate.CandidateStatus.INTERESTED),
        ),
        manual_under_review_candidates=Count(
            'id_candidate',
            filter=Q(source=ResearchCandidate.Source.MANUAL, status=ResearchCandidate.CandidateStatus.UNDER_REVIEW),
        ),
        manual_approved_candidates=Count(
            'id_candidate',
            filter=Q(source=ResearchCandidate.Source.MANUAL, status=ResearchCandidate.CandidateStatus.APPROVED),
        ),
        manual_rejected_candidates=Count(
            'id_candidate',
            filter=Q(source=ResearchCandidate.Source.MANUAL, status=ResearchCandidate.CandidateStatus.REJECTED),
        ),
        interest_suggested_candidates=Count(
            'id_candidate',
            filter=Q(source=ResearchCandidate.Source.INTEREST, status=ResearchCandidate.CandidateStatus.SUGGESTED),
        ),
        interest_interested_candidates=Count(
            'id_candidate',
            filter=Q(source=ResearchCandidate.Source.INTEREST, status=ResearchCandidate.CandidateStatus.INTERESTED),
        ),
        interest_under_review_candidates=Count(
            'id_candidate',
            filter=Q(source=ResearchCandidate.Source.INTEREST, status=ResearchCandidate.CandidateStatus.UNDER_REVIEW),
        ),
        interest_approved_candidates=Count(
            'id_candidate',
            filter=Q(source=ResearchCandidate.Source.INTEREST, status=ResearchCandidate.CandidateStatus.APPROVED),
        ),
        interest_rejected_candidates=Count(
            'id_candidate',
            filter=Q(source=ResearchCandidate.Source.INTEREST, status=ResearchCandidate.CandidateStatus.REJECTED),
        ),
    )


def _candidate_source_status_rows(summary):
    return [
        {
            'source': ResearchCandidate.Source.AI,
            'status': ResearchCandidate.CandidateStatus.SUGGESTED,
            'count': summary['ai_suggested_candidates'] or 0,
        },
        {
            'source': ResearchCandidate.Source.AI,
            'status': ResearchCandidate.CandidateStatus.INTERESTED,
            'count': summary['ai_interested_candidates'] or 0,
        },
        {
            'source': ResearchCandidate.Source.AI,
            'status': ResearchCandidate.CandidateStatus.UNDER_REVIEW,
            'count': summary['ai_under_review_candidates'] or 0,
        },
        {
            'source': ResearchCandidate.Source.AI,
            'status': ResearchCandidate.CandidateStatus.APPROVED,
            'count': summary['ai_approved_candidates'] or 0,
        },
        {
            'source': ResearchCandidate.Source.AI,
            'status': ResearchCandidate.CandidateStatus.REJECTED,
            'count': summary['ai_rejected_candidates'] or 0,
        },
        {
            'source': ResearchCandidate.Source.MANUAL,
            'status': ResearchCandidate.CandidateStatus.SUGGESTED,
            'count': summary['manual_suggested_candidates'] or 0,
        },
        {
            'source': ResearchCandidate.Source.MANUAL,
            'status': ResearchCandidate.CandidateStatus.INTERESTED,
            'count': summary['manual_interested_candidates'] or 0,
        },
        {
            'source': ResearchCandidate.Source.MANUAL,
            'status': ResearchCandidate.CandidateStatus.UNDER_REVIEW,
            'count': summary['manual_under_review_candidates'] or 0,
        },
        {
            'source': ResearchCandidate.Source.MANUAL,
            'status': ResearchCandidate.CandidateStatus.APPROVED,
            'count': summary['manual_approved_candidates'] or 0,
        },
        {
            'source': ResearchCandidate.Source.MANUAL,
            'status': ResearchCandidate.CandidateStatus.REJECTED,
            'count': summary['manual_rejected_candidates'] or 0,
        },
        {
            'source': ResearchCandidate.Source.INTEREST,
            'status': ResearchCandidate.CandidateStatus.SUGGESTED,
            'count': summary['interest_suggested_candidates'] or 0,
        },
        {
            'source': ResearchCandidate.Source.INTEREST,
            'status': ResearchCandidate.CandidateStatus.INTERESTED,
            'count': summary['interest_interested_candidates'] or 0,
        },
        {
            'source': ResearchCandidate.Source.INTEREST,
            'status': ResearchCandidate.CandidateStatus.UNDER_REVIEW,
            'count': summary['interest_under_review_candidates'] or 0,
        },
        {
            'source': ResearchCandidate.Source.INTEREST,
            'status': ResearchCandidate.CandidateStatus.APPROVED,
            'count': summary['interest_approved_candidates'] or 0,
        },
        {
            'source': ResearchCandidate.Source.INTEREST,
            'status': ResearchCandidate.CandidateStatus.REJECTED,
            'count': summary['interest_rejected_candidates'] or 0,
        },
    ]


class ResearcherDashboardView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.id_type != User.UserType.PESQUISADOR or not hasattr(user, 'researcher_profile'):
            raise PermissionDenied('Apenas usuarios pesquisador podem acessar este painel.')

        queryset = ResearchCandidate.objects.select_related('research', 'research__company', 'research__area').filter(
            researcher=user.researcher_profile
        )

        summary = _candidate_breakdown_summary(queryset)

        top_companies_rows = (
            queryset.values('research__company_id', 'research__company__legal_name', 'research__company__name')
            .annotate(candidate_count=Count('id_candidate'), average_score=Avg('score_match'))
            .order_by('-candidate_count', '-average_score')[:5]
        )
        top_areas_rows = (
            queryset.values('research__area_id', 'research__area__name')
            .annotate(candidate_count=Count('id_candidate'), average_score=Avg('score_match'))
            .order_by('-candidate_count', '-average_score')[:5]
        )

        payload = {
            'summary': {
                'total_candidates': summary['total_candidates'] or 0,
                'average_score': _float_or_none(summary['average_score']),
                'ai_suggested_candidates': summary['ai_suggested_candidates'] or 0,
                'ai_interested_candidates': summary['ai_interested_candidates'] or 0,
                'ai_under_review_candidates': summary['ai_under_review_candidates'] or 0,
                'ai_approved_candidates': summary['ai_approved_candidates'] or 0,
                'ai_rejected_candidates': summary['ai_rejected_candidates'] or 0,
                'manual_suggested_candidates': summary['manual_suggested_candidates'] or 0,
                'manual_interested_candidates': summary['manual_interested_candidates'] or 0,
                'manual_under_review_candidates': summary['manual_under_review_candidates'] or 0,
                'manual_approved_candidates': summary['manual_approved_candidates'] or 0,
                'manual_rejected_candidates': summary['manual_rejected_candidates'] or 0,
                'interest_suggested_candidates': summary['interest_suggested_candidates'] or 0,
                'interest_interested_candidates': summary['interest_interested_candidates'] or 0,
                'interest_under_review_candidates': summary['interest_under_review_candidates'] or 0,
                'interest_approved_candidates': summary['interest_approved_candidates'] or 0,
                'interest_rejected_candidates': summary['interest_rejected_candidates'] or 0,
            },
            'by_source': [
                {'source': ResearchCandidate.Source.MANUAL, 'count': (summary['manual_suggested_candidates'] or 0) + (summary['manual_interested_candidates'] or 0) + (summary['manual_under_review_candidates'] or 0) + (summary['manual_approved_candidates'] or 0) + (summary['manual_rejected_candidates'] or 0)},
                {'source': ResearchCandidate.Source.AI, 'count': (summary['ai_suggested_candidates'] or 0) + (summary['ai_interested_candidates'] or 0) + (summary['ai_under_review_candidates'] or 0) + (summary['ai_approved_candidates'] or 0) + (summary['ai_rejected_candidates'] or 0)},
                {'source': ResearchCandidate.Source.INTEREST, 'count': (summary['interest_suggested_candidates'] or 0) + (summary['interest_interested_candidates'] or 0) + (summary['interest_under_review_candidates'] or 0) + (summary['interest_approved_candidates'] or 0) + (summary['interest_rejected_candidates'] or 0)},
            ],
            'by_status': [
                {'status': ResearchCandidate.CandidateStatus.SUGGESTED, 'count': (summary['ai_suggested_candidates'] or 0) + (summary['manual_suggested_candidates'] or 0) + (summary['interest_suggested_candidates'] or 0)},
                {'status': ResearchCandidate.CandidateStatus.INTERESTED, 'count': (summary['ai_interested_candidates'] or 0) + (summary['manual_interested_candidates'] or 0) + (summary['interest_interested_candidates'] or 0)},
                {'status': ResearchCandidate.CandidateStatus.UNDER_REVIEW, 'count': (summary['ai_under_review_candidates'] or 0) + (summary['manual_under_review_candidates'] or 0) + (summary['interest_under_review_candidates'] or 0)},
                {'status': ResearchCandidate.CandidateStatus.APPROVED, 'count': (summary['ai_approved_candidates'] or 0) + (summary['manual_approved_candidates'] or 0) + (summary['interest_approved_candidates'] or 0)},
                {'status': ResearchCandidate.CandidateStatus.REJECTED, 'count': (summary['ai_rejected_candidates'] or 0) + (summary['manual_rejected_candidates'] or 0) + (summary['interest_rejected_candidates'] or 0)},
            ],
            'by_source_status': _candidate_source_status_rows(summary),
            'top_companies': [
                {
                    'company_id': row['research__company_id'],
                    'company_name': row['research__company__legal_name'] or row['research__company__name'],
                    'count': row['candidate_count'],
                    'average_score': _float_or_none(row['average_score']),
                }
                for row in top_companies_rows
            ],
            'top_areas': [
                {
                    'area_id': row['research__area_id'],
                    'area_name': row['research__area__name'],
                    'count': row['candidate_count'],
                    'average_score': _float_or_none(row['average_score']),
                }
                for row in top_areas_rows
            ],
        }
        return response.Response(payload, status=status.HTTP_200_OK)


class CompanyDashboardView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.id_type != User.UserType.EMPRESA or not hasattr(user, 'company_profile'):
            raise PermissionDenied('Apenas usuarios empresa podem acessar este painel.')

        company = user.company_profile
        research_id = _parse_optional_int(request.query_params.get('research_id'), 'research_id')

        candidate_qs = ResearchCandidate.objects.select_related('research', 'research__company', 'research__area').filter(
            research__company=company
        )
        research_qs = Research.objects.select_related('area').filter(company=company)

        if research_id is not None:
            get_object_or_404(Research, pk=research_id, company=company)
            candidate_qs = candidate_qs.filter(research_id=research_id)
            research_qs = research_qs.filter(pk=research_id)

        summary = _candidate_breakdown_summary(candidate_qs)

        research_rows = research_qs.annotate(
            total_candidates=Count('candidates', filter=Q(candidates__isnull=False)),
            average_score=Avg('candidates__score_match'),
            manual_candidates=Count('candidates', filter=Q(candidates__source=ResearchCandidate.Source.MANUAL)),
            ai_candidates=Count('candidates', filter=Q(candidates__source=ResearchCandidate.Source.AI)),
            interest_candidates=Count('candidates', filter=Q(candidates__source=ResearchCandidate.Source.INTEREST)),
            suggested_candidates=Count('candidates', filter=Q(candidates__status=ResearchCandidate.CandidateStatus.SUGGESTED)),
            interested_candidates=Count('candidates', filter=Q(candidates__status=ResearchCandidate.CandidateStatus.INTERESTED)),
            under_review_candidates=Count('candidates', filter=Q(candidates__status=ResearchCandidate.CandidateStatus.UNDER_REVIEW)),
            approved_candidates=Count('candidates', filter=Q(candidates__status=ResearchCandidate.CandidateStatus.APPROVED)),
            rejected_candidates=Count('candidates', filter=Q(candidates__status=ResearchCandidate.CandidateStatus.REJECTED)),
        ).order_by('-total_candidates', '-average_score', '-update_date')

        payload = {
            'summary': {
                'total_researches': research_qs.count(),
                'total_candidates': summary['total_candidates'] or 0,
                'average_score': _float_or_none(summary['average_score']),
                'ai_suggested_candidates': summary['ai_suggested_candidates'] or 0,
                'ai_interested_candidates': summary['ai_interested_candidates'] or 0,
                'ai_under_review_candidates': summary['ai_under_review_candidates'] or 0,
                'ai_approved_candidates': summary['ai_approved_candidates'] or 0,
                'ai_rejected_candidates': summary['ai_rejected_candidates'] or 0,
                'manual_suggested_candidates': summary['manual_suggested_candidates'] or 0,
                'manual_interested_candidates': summary['manual_interested_candidates'] or 0,
                'manual_under_review_candidates': summary['manual_under_review_candidates'] or 0,
                'manual_approved_candidates': summary['manual_approved_candidates'] or 0,
                'manual_rejected_candidates': summary['manual_rejected_candidates'] or 0,
                'interest_suggested_candidates': summary['interest_suggested_candidates'] or 0,
                'interest_interested_candidates': summary['interest_interested_candidates'] or 0,
                'interest_under_review_candidates': summary['interest_under_review_candidates'] or 0,
                'interest_approved_candidates': summary['interest_approved_candidates'] or 0,
                'interest_rejected_candidates': summary['interest_rejected_candidates'] or 0,
            },
            'by_source': [
                {'source': ResearchCandidate.Source.MANUAL, 'count': (summary['manual_suggested_candidates'] or 0) + (summary['manual_interested_candidates'] or 0) + (summary['manual_under_review_candidates'] or 0) + (summary['manual_approved_candidates'] or 0) + (summary['manual_rejected_candidates'] or 0)},
                {'source': ResearchCandidate.Source.AI, 'count': (summary['ai_suggested_candidates'] or 0) + (summary['ai_interested_candidates'] or 0) + (summary['ai_under_review_candidates'] or 0) + (summary['ai_approved_candidates'] or 0) + (summary['ai_rejected_candidates'] or 0)},
                {'source': ResearchCandidate.Source.INTEREST, 'count': (summary['interest_suggested_candidates'] or 0) + (summary['interest_interested_candidates'] or 0) + (summary['interest_under_review_candidates'] or 0) + (summary['interest_approved_candidates'] or 0) + (summary['interest_rejected_candidates'] or 0)},
            ],
            'by_status': [
                {'status': ResearchCandidate.CandidateStatus.SUGGESTED, 'count': (summary['ai_suggested_candidates'] or 0) + (summary['manual_suggested_candidates'] or 0) + (summary['interest_suggested_candidates'] or 0)},
                {'status': ResearchCandidate.CandidateStatus.INTERESTED, 'count': (summary['ai_interested_candidates'] or 0) + (summary['manual_interested_candidates'] or 0) + (summary['interest_interested_candidates'] or 0)},
                {'status': ResearchCandidate.CandidateStatus.UNDER_REVIEW, 'count': (summary['ai_under_review_candidates'] or 0) + (summary['manual_under_review_candidates'] or 0) + (summary['interest_under_review_candidates'] or 0)},
                {'status': ResearchCandidate.CandidateStatus.APPROVED, 'count': (summary['ai_approved_candidates'] or 0) + (summary['manual_approved_candidates'] or 0) + (summary['interest_approved_candidates'] or 0)},
                {'status': ResearchCandidate.CandidateStatus.REJECTED, 'count': (summary['ai_rejected_candidates'] or 0) + (summary['manual_rejected_candidates'] or 0) + (summary['interest_rejected_candidates'] or 0)},
            ],
            'by_source_status': _candidate_source_status_rows(summary),
            'researches': [
                {
                    'research_id': row.id_research,
                    'title': row.title,
                    'status': row.status,
                    'area': row.area.name if row.area_id else None,
                    'total_candidates': row.total_candidates,
                    'average_score': _float_or_none(row.average_score),
                    'manual_candidates': row.manual_candidates,
                    'ai_candidates': row.ai_candidates,
                    'interest_candidates': row.interest_candidates,
                    'suggested_candidates': row.suggested_candidates,
                    'interested_candidates': row.interested_candidates,
                    'under_review_candidates': row.under_review_candidates,
                    'approved_candidates': row.approved_candidates,
                    'rejected_candidates': row.rejected_candidates,
                }
                for row in research_rows
            ],
        }
        return response.Response(payload, status=status.HTTP_200_OK)


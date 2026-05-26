from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.research.models import Research
from apps.research_candidates.models import ResearchCandidate
from apps.researchers.models import Researcher
from apps.search.services import (
    build_research_search_text,
    build_researcher_search_text,
    search_research,
    search_researchers,
)


MATCH_LIMIT_PER_RESEARCH = int(getattr(settings, 'AI_MATCH_LIMIT_PER_RESEARCH', 30))
MATCH_LIMIT_PER_RESEARCHER = int(getattr(settings, 'AI_MATCH_LIMIT_PER_RESEARCHER', 30))
MATCH_MIN_SCORE = float(getattr(settings, 'AI_MATCH_MIN_SCORE', 0.30))
WEIGHT_SEMANTIC = float(getattr(settings, 'AI_MATCH_WEIGHT_SEMANTIC', 0.50))
WEIGHT_LEXICAL = float(getattr(settings, 'AI_MATCH_WEIGHT_LEXICAL', 0.25))
WEIGHT_AREA = float(getattr(settings, 'AI_MATCH_WEIGHT_AREA', 0.15))
WEIGHT_AVAILABILITY = float(getattr(settings, 'AI_MATCH_WEIGHT_AVAILABILITY', 0.10))
OPEN_RESEARCH_STATUS = {'aberta', 'aberto', 'ativa', 'ativo', 'open'}


def _normalize_score(value):
    return max(0.0, min(1.0, float(value)))


def _is_open_research_status(status):
    return str(status or '').strip().lower() in OPEN_RESEARCH_STATUS


def _to_decimal_score(value):
    score = _normalize_score(value)
    return Decimal(str(score)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)


def _candidate_reasons(semantic, lexical, area_score, availability_score):
    reasons = []
    if semantic >= 0.65:
        reasons.append('alta_similaridade_semantica')
    elif semantic >= 0.45:
        reasons.append('similaridade_semantica_moderada')

    if lexical >= 0.20:
        reasons.append('boa_aderencia_textual')

    if area_score >= 1.0:
        reasons.append('mesma_area_de_pesquisa')

    if availability_score >= 1.0:
        reasons.append('pesquisador_disponivel')

    if not reasons:
        reasons.append('compatibilidade_geral')
    return reasons


def _final_score(semantic, lexical, area_score, availability_score):
    return _normalize_score(
        semantic * WEIGHT_SEMANTIC
        + lexical * WEIGHT_LEXICAL
        + area_score * WEIGHT_AREA
        + availability_score * WEIGHT_AVAILABILITY
    )


def _upsert_ai_candidate(
    research,
    researcher,
    score,
    semantic,
    lexical,
    area_score,
    availability_score,
    reasons,
    run_id,
):
    defaults = {
        'source': ResearchCandidate.Source.AI,
        'status': ResearchCandidate.CandidateStatus.SUGGESTED,
        'score_match': _to_decimal_score(score),
        'ai_run_id': run_id,
        'match_reasons': reasons,
        'score_features': {
            'semantic': round(float(semantic), 4),
            'lexical': round(float(lexical), 4),
            'area': round(float(area_score), 4),
            'availability': round(float(availability_score), 4),
        },
    }
    candidate, created = ResearchCandidate.objects.get_or_create(
        research=research,
        researcher=researcher,
        defaults=defaults,
    )
    if created:
        return candidate, True, True

    if candidate.source in {ResearchCandidate.Source.INTEREST, ResearchCandidate.Source.MANUAL}:
        return candidate, False, False

    candidate.source = ResearchCandidate.Source.AI
    candidate.score_match = defaults['score_match']
    candidate.ai_run_id = run_id
    candidate.match_reasons = defaults['match_reasons']
    candidate.score_features = defaults['score_features']
    if candidate.status == ResearchCandidate.CandidateStatus.SUGGESTED:
        candidate.status = ResearchCandidate.CandidateStatus.SUGGESTED
    candidate.save(
        update_fields=[
            'source',
            'score_match',
            'ai_run_id',
            'match_reasons',
            'score_features',
            'updated_at',
        ]
    )
    return candidate, False, True


@transaction.atomic
def run_match_for_research(research_id, limit=None):
    research = (
        Research.objects.select_related('area', 'company')
        .prefetch_related('area')
        .filter(pk=research_id)
        .first()
    )
    if not research:
        return {'ok': False, 'detail': 'research_not_found'}

    if not _is_open_research_status(research.status):
        removed = ResearchCandidate.objects.filter(
            research=research,
            source=ResearchCandidate.Source.AI,
            status=ResearchCandidate.CandidateStatus.SUGGESTED,
        ).delete()[0]
        return {
            'ok': True,
            'run_id': None,
            'updated': 0,
            'removed': removed,
            'generated_at': timezone.now(),
        }

    run_id = uuid4()
    max_items = limit or MATCH_LIMIT_PER_RESEARCH
    query_text = build_research_search_text(research)
    rows = search_researchers(
        query_text=query_text,
        area_id=None,
        available=None,
        limit=max_items,
    )

    researchers = {
        row['id_researcher']: row
        for row in rows
    }
    researcher_objs = {
        obj.id_researcher: obj
        for obj in Researcher.objects.prefetch_related('area').filter(id_researcher__in=researchers.keys())
    }

    kept_ids = set()
    updated = 0
    for researcher_id, row in researchers.items():
        researcher = researcher_objs.get(researcher_id)
        if not researcher:
            continue

        semantic = _normalize_score(row.get('score_semantic', 0.0))
        lexical = _normalize_score(row.get('score_lexical', 0.0))
        area_score = 1.0 if researcher.area.filter(id_area=research.area_id).exists() else 0.0
        if researcher.availability is True:
            availability_score = 1.0
        elif researcher.availability is None:
            availability_score = 0.4
        else:
            availability_score = 0.0

        final_score = _final_score(semantic, lexical, area_score, availability_score)
        if final_score < MATCH_MIN_SCORE:
            continue

        reasons = _candidate_reasons(semantic, lexical, area_score, availability_score)
        candidate, _, changed = _upsert_ai_candidate(
            research=research,
            researcher=researcher,
            score=final_score,
            semantic=semantic,
            lexical=lexical,
            area_score=area_score,
            availability_score=availability_score,
            reasons=reasons,
            run_id=run_id,
        )
        kept_ids.add(candidate.id_candidate)
        if changed:
            updated += 1

    stale_ai = ResearchCandidate.objects.filter(
        research=research,
        source=ResearchCandidate.Source.AI,
        status=ResearchCandidate.CandidateStatus.SUGGESTED,
    ).exclude(id_candidate__in=kept_ids)
    removed = stale_ai.count()
    stale_ai.delete()

    return {
        'ok': True,
        'run_id': run_id,
        'updated': updated,
        'removed': removed,
        'generated_at': timezone.now(),
    }


@transaction.atomic
def run_match_for_researcher(researcher_id, limit=None):
    researcher = (
        Researcher.objects.select_related('university', 'resume')
        .prefetch_related('area', 'resume__skill')
        .filter(pk=researcher_id)
        .first()
    )
    if not researcher:
        return {'ok': False, 'detail': 'researcher_not_found'}

    run_id = uuid4()
    max_items = limit or MATCH_LIMIT_PER_RESEARCHER
    query_text = build_researcher_search_text(researcher)
    rows = search_research(
        query_text=query_text,
        area_id=None,
        open_only=True,
        limit=max_items,
    )

    research_rows = {row['id_research']: row for row in rows}
    research_objs = {
        obj.id_research: obj
        for obj in Research.objects.select_related('area').filter(id_research__in=research_rows.keys())
    }
    researcher_area_ids = set(researcher.area.values_list('id_area', flat=True))

    kept_ids = set()
    updated = 0
    for research_id, row in research_rows.items():
        research = research_objs.get(research_id)
        if not research:
            continue

        semantic = _normalize_score(row.get('score_semantic', 0.0))
        lexical = _normalize_score(row.get('score_lexical', 0.0))
        area_score = 1.0 if research.area_id in researcher_area_ids else 0.0
        if researcher.availability is True:
            availability_score = 1.0
        elif researcher.availability is None:
            availability_score = 0.4
        else:
            availability_score = 0.0

        final_score = _final_score(semantic, lexical, area_score, availability_score)
        if final_score < MATCH_MIN_SCORE:
            continue

        reasons = _candidate_reasons(semantic, lexical, area_score, availability_score)
        candidate, _, changed = _upsert_ai_candidate(
            research=research,
            researcher=researcher,
            score=final_score,
            semantic=semantic,
            lexical=lexical,
            area_score=area_score,
            availability_score=availability_score,
            reasons=reasons,
            run_id=run_id,
        )
        kept_ids.add(candidate.id_candidate)
        if changed:
            updated += 1

    stale_ai = ResearchCandidate.objects.filter(
        researcher=researcher,
        source=ResearchCandidate.Source.AI,
        status=ResearchCandidate.CandidateStatus.SUGGESTED,
    ).exclude(id_candidate__in=kept_ids)
    removed = stale_ai.count()
    stale_ai.delete()

    return {
        'ok': True,
        'run_id': run_id,
        'updated': updated,
        'removed': removed,
        'generated_at': timezone.now(),
    }

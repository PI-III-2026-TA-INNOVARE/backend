import json
import logging
import re
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from django.conf import settings
from django.db import transaction
from django.utils import timezone
import httpx

from apps.research.models import Research
from apps.research_candidates.models import ResearchCandidate
from apps.researchers.models import Researcher
from apps.search.services import (
    build_research_search_text,
    build_researcher_search_text,
    search_research,
    search_researchers,
)

logger = logging.getLogger(__name__)

MATCH_LIMIT_PER_RESEARCH = int(getattr(settings, 'AI_MATCH_LIMIT_PER_RESEARCH', 30))
MATCH_LIMIT_PER_RESEARCHER = int(getattr(settings, 'AI_MATCH_LIMIT_PER_RESEARCHER', 30))
MATCH_MIN_SCORE = float(getattr(settings, 'AI_MATCH_MIN_SCORE', 0.30))
WEIGHT_SEMANTIC = float(getattr(settings, 'AI_MATCH_WEIGHT_SEMANTIC', 0.50))
WEIGHT_LEXICAL = float(getattr(settings, 'AI_MATCH_WEIGHT_LEXICAL', 0.25))
WEIGHT_AREA = float(getattr(settings, 'AI_MATCH_WEIGHT_AREA', 0.15))
WEIGHT_AVAILABILITY = float(getattr(settings, 'AI_MATCH_WEIGHT_AVAILABILITY', 0.10))
OPEN_RESEARCH_STATUS = {'aberta', 'aberto', 'ativa', 'ativo', 'open'}
REQUIRE_STRONG_REASON = bool(getattr(settings, 'AI_MATCH_REQUIRE_STRONG_REASON', True))
RERANK_ENABLED = bool(getattr(settings, 'AI_MATCH_RERANK_ENABLED', False))
RERANK_TOP_N = int(getattr(settings, 'AI_MATCH_RERANK_TOP_N', 12))
RERANK_WEIGHT = float(getattr(settings, 'AI_MATCH_RERANK_WEIGHT', 0.35))
GEMINI_API_KEY = getattr(settings, 'GEMINI_API_KEY', '') or ''
GEMINI_MODEL = getattr(settings, 'AI_MATCH_GEMINI_MODEL', 'gemini-2.5-flash')
GEMINI_TIMEOUT_SECONDS = int(getattr(settings, 'AI_MATCH_GEMINI_TIMEOUT_SECONDS', 25))

JSON_BLOCK_RE = re.compile(r'\{.*\}', re.DOTALL)


def _normalize_score(value):
    return max(0.0, min(1.0, float(value)))


def _extract_json_object(raw_text):
    if not raw_text:
        return None
    content = raw_text.strip()
    if content.startswith('```'):
        content = content.strip('`')
        if content.startswith('json'):
            content = content[4:].strip()
    try:
        return json.loads(content)
    except Exception:
        pass

    match = JSON_BLOCK_RE.search(raw_text)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


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


def _has_strong_reason(semantic, lexical, area_score):
    return bool(semantic >= 0.45 or lexical >= 0.20 or area_score >= 1.0)


def _should_rerank_with_gemini():
    return bool(RERANK_ENABLED and GEMINI_API_KEY)


def _gemini_rerank(reference_text, candidates, direction):
    if not _should_rerank_with_gemini():
        return {}
    if not candidates:
        return {}

    endpoint = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent'
    prompt = (
        'Você é um reranker técnico para match de P&D.\n'
        f'Direção do match: {direction}.\n'
        'Analise a referência e os candidatos e atribua score de 0 a 1 de compatibilidade técnica.\n'
        'Considere aderência de área, contexto semântico, habilidades e experiência.\n'
        'Retorne APENAS JSON no formato:\n'
        '{"items":[{"id":"<id>","score":0.0,"reason":"<motivo_curto>"}]}\n\n'
        f'Referência:\n{reference_text}\n\n'
        f'Candidatos:\n{json.dumps(candidates, ensure_ascii=False)}'
    )

    payload = {
        'contents': [
            {
                'parts': [
                    {'text': prompt}
                ]
            }
        ],
        'generationConfig': {
            'temperature': 0.0,
            'topP': 0.1,
            'responseMimeType': 'application/json',
        }
    }

    try:
        with httpx.Client(timeout=GEMINI_TIMEOUT_SECONDS) as client:
            resp = client.post(
                endpoint,
                headers={
                    'Content-Type': 'application/json',
                    'x-goog-api-key': GEMINI_API_KEY,
                },
                json=payload,
            )
            resp.raise_for_status()
            body = resp.json()
    except Exception as exc:
        logger.warning('Gemini rerank indisponivel. Usando somente base MiniLM. erro=%s', exc)
        return {}

    text_parts = []
    for cand in body.get('candidates', []):
        for part in cand.get('content', {}).get('parts', []):
            txt = part.get('text')
            if txt:
                text_parts.append(txt)
    parsed = _extract_json_object('\n'.join(text_parts))
    if not parsed or not isinstance(parsed.get('items'), list):
        logger.warning('Gemini rerank retornou formato invalido. Usando somente base MiniLM.')
        return {}

    results = {}
    for item in parsed['items']:
        cid = str(item.get('id', '')).strip()
        if not cid:
            continue
        results[cid] = {
            'llm_score': _normalize_score(item.get('score', 0.0)),
            'llm_reason': str(item.get('reason', '')).strip()[:240],
        }
    return results


def _final_score(semantic, lexical, area_score, availability_score):
    return _normalize_score(
        semantic * WEIGHT_SEMANTIC
        + lexical * WEIGHT_LEXICAL
        + area_score * WEIGHT_AREA
        + availability_score * WEIGHT_AVAILABILITY
    )


def _final_score_with_rerank(base_score, llm_score):
    return _normalize_score((1.0 - RERANK_WEIGHT) * _normalize_score(base_score) + RERANK_WEIGHT * _normalize_score(llm_score))


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
    llm_score=None,
    llm_reason=None,
):
    features = {
        'semantic': round(float(semantic), 4),
        'lexical': round(float(lexical), 4),
        'area': round(float(area_score), 4),
        'availability': round(float(availability_score), 4),
    }
    if llm_score is not None:
        features['llm'] = round(float(llm_score), 4)
    if llm_reason:
        features['llm_reason'] = str(llm_reason)[:240]

    defaults = {
        'source': ResearchCandidate.Source.AI,
        'status': ResearchCandidate.CandidateStatus.SUGGESTED,
        'score_match': _to_decimal_score(score),
        'ai_run_id': run_id,
        'match_reasons': reasons,
        'score_features': features,
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

    rerank_pool = []
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
        base_score = _final_score(semantic, lexical, area_score, availability_score)
        rerank_pool.append(
            {
                'id': str(researcher_id),
                'summary': build_researcher_search_text(researcher),
                'base_score': base_score,
            }
        )
    rerank_pool.sort(key=lambda item: item['base_score'], reverse=True)
    rerank_inputs = [
        {'id': item['id'], 'summary': item['summary']}
        for item in rerank_pool[:RERANK_TOP_N]
    ]
    rerank_results = _gemini_rerank(
        reference_text=query_text,
        candidates=rerank_inputs,
        direction='research_to_researcher',
    )

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
        if REQUIRE_STRONG_REASON and not _has_strong_reason(semantic, lexical, area_score):
            continue

        reasons = _candidate_reasons(semantic, lexical, area_score, availability_score)
        llm_payload = rerank_results.get(str(researcher_id))
        llm_score = None
        llm_reason = None
        if llm_payload:
            llm_score = llm_payload.get('llm_score')
            llm_reason = llm_payload.get('llm_reason')
            final_score = _final_score_with_rerank(final_score, llm_score)
            if llm_reason:
                reasons.append('gemini_rerank')
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
            llm_score=llm_score,
            llm_reason=llm_reason,
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

    rerank_pool = []
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
        base_score = _final_score(semantic, lexical, area_score, availability_score)
        rerank_pool.append(
            {
                'id': str(research_id),
                'summary': build_research_search_text(research),
                'base_score': base_score,
            }
        )
    rerank_pool.sort(key=lambda item: item['base_score'], reverse=True)
    rerank_inputs = [
        {'id': item['id'], 'summary': item['summary']}
        for item in rerank_pool[:RERANK_TOP_N]
    ]
    rerank_results = _gemini_rerank(
        reference_text=query_text,
        candidates=rerank_inputs,
        direction='researcher_to_research',
    )

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
        if REQUIRE_STRONG_REASON and not _has_strong_reason(semantic, lexical, area_score):
            continue

        reasons = _candidate_reasons(semantic, lexical, area_score, availability_score)
        llm_payload = rerank_results.get(str(research_id))
        llm_score = None
        llm_reason = None
        if llm_payload:
            llm_score = llm_payload.get('llm_score')
            llm_reason = llm_payload.get('llm_reason')
            final_score = _final_score_with_rerank(final_score, llm_score)
            if llm_reason:
                reasons.append('gemini_rerank')
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
            llm_score=llm_score,
            llm_reason=llm_reason,
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

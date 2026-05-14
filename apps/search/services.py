import hashlib
import logging
import math
import re
import unicodedata
from functools import lru_cache

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import F, Q, Value
from pgvector.django import CosineDistance

from apps.educations.models import Education
from apps.experiences.models import Experience
from apps.research.models import Research
from apps.researchers.models import Researcher
from apps.search.models import SearchResearchIndex, SearchResearcherIndex

logger = logging.getLogger(__name__)
TOKEN_SPLIT_RE = re.compile(r'[^a-zA-Z0-9_]+')
DEFAULT_MIN_HYBRID_SCORE = float(getattr(settings, 'SEARCH_MIN_HYBRID_SCORE', 0.28))
DEFAULT_RELATIVE_CUTOFF = float(getattr(settings, 'SEARCH_RELATIVE_CUTOFF', 0.65))


def _tokenize(text):
    normalized = _normalize_for_search(text)
    return [token for token in TOKEN_SPLIT_RE.split(normalized) if token]


def _normalize_spaces(text):
    return re.sub(r'\s+', ' ', (text or '')).strip()


def _strip_accents(text):
    decomposed = unicodedata.normalize('NFD', text or '')
    return ''.join(ch for ch in decomposed if unicodedata.category(ch) != 'Mn')


def _normalize_for_search(text):
    return _normalize_spaces(_strip_accents((text or '').lower()))


def _with_normalized_variant(text):
    raw = _normalize_spaces(text)
    normalized = _normalize_for_search(raw)
    if not raw:
        return normalized
    if normalized == raw.lower():
        return raw
    return _normalize_spaces(f'{raw} {normalized}')


def _apply_relevance_cutoff(rows, limit, min_hybrid=None, relative_cutoff=None):
    if not rows:
        return []

    min_hybrid = (
        DEFAULT_MIN_HYBRID_SCORE if min_hybrid is None else float(min_hybrid)
    )
    relative_cutoff = (
        DEFAULT_RELATIVE_CUTOFF if relative_cutoff is None else float(relative_cutoff)
    )

    rows.sort(key=lambda row: row['score_hybrid'], reverse=True)
    best_score = rows[0]['score_hybrid']
    threshold = max(min_hybrid, best_score * relative_cutoff)

    filtered = [row for row in rows if row['score_hybrid'] >= threshold]
    return filtered[:limit]


def _fit_dimension(vector, dim):
    if len(vector) == dim:
        return vector
    if len(vector) > dim:
        return vector[:dim]
    return vector + [0.0] * (dim - len(vector))


def _hash_embedding(text, dimension):
    vec = [0.0] * dimension
    tokens = _tokenize(text)
    if not tokens:
        return vec

    for token in tokens:
        digest = hashlib.sha256(token.encode('utf-8')).digest()
        slot = int.from_bytes(digest[:4], 'big') % dimension
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        weight = 1.0 + (digest[5] / 255.0)
        vec[slot] += sign * weight

    norm = math.sqrt(sum(v * v for v in vec))
    if norm <= 0:
        return vec
    return [v / norm for v in vec]


@lru_cache(maxsize=1)
def _load_embedding_model():
    model_name = getattr(
        settings,
        'SEARCH_EMBEDDING_MODEL',
        'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
    )
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def build_embedding(text, dimension=None):
    dim = dimension or settings.SEARCH_EMBEDDING_DIMENSION
    normalized_text = (text or '').strip()
    if not normalized_text:
        return [0.0] * dim

    try:
        model = _load_embedding_model()
        vec = model.encode(normalized_text, normalize_embeddings=True).tolist()
        return _fit_dimension(vec, dim)
    except Exception as exc:
        if not getattr(settings, 'SEARCH_EMBEDDING_ALLOW_HASH_FALLBACK', True):
            raise
        logger.warning('MiniLM embedding falhou; usando fallback hash local. Erro: %s', exc)
        return _hash_embedding(normalized_text, dim)


def build_researcher_search_text(researcher):
    area_names = list(researcher.area.values_list('name', flat=True))
    university_name = researcher.university.name if researcher.university_id else ''

    skills = []
    educations = []
    experiences = []

    if researcher.resume_id:
        resume = researcher.resume
        skills = list(resume.skill.values_list('description', flat=True))
        educations = list(
            Education.objects.filter(resume_id=researcher.resume_id).values_list('course', 'institution')
        )
        experiences = list(
            Experience.objects.filter(resume_id=researcher.resume_id).values_list('description', flat=True)
        )

    education_chunks = [f'{course} {institution}' for course, institution in educations]

    chunks = [
        researcher.name or '',
        university_name or '',
        ' '.join(area_names),
        ' '.join(skills),
        ' '.join(education_chunks),
        ' '.join(experiences),
    ]
    return _with_normalized_variant(' '.join(chunks))


def build_research_search_text(research):
    area_name = research.area.name if research.area_id else ''
    company = research.company if research.company_id else None
    company_name = ''
    company_location = ''
    if company:
        company_name = company.legal_name or company.name or ''
        city = company.city or ''
        state = company.state or ''
        company_location = _normalize_spaces(f'{city} {state}')

    chunks = [
        research.title or '',
        research.scope or '',
        research.goal or '',
        research.justification or '',
        research.results or '',
        area_name,
        company_name,
        company_location,
    ]
    return _with_normalized_variant(' '.join(chunks))


def upsert_researcher_index(researcher_id):
    researcher = (
        Researcher.objects.select_related('university', 'resume')
        .prefetch_related('area', 'resume__skill')
        .filter(pk=researcher_id)
        .first()
    )
    if not researcher:
        SearchResearcherIndex.objects.filter(researcher_id=researcher_id).delete()
        return

    text = build_researcher_search_text(researcher)
    embedding = build_embedding(text)

    obj, _ = SearchResearcherIndex.objects.get_or_create(researcher=researcher)
    obj.search_text = text
    obj.embedding = embedding
    obj.save(update_fields=['search_text', 'embedding', 'updated_at'])

    SearchResearcherIndex.objects.filter(researcher=researcher).update(
        search_tsv=SearchVector(Value(text), config='portuguese')
    )


def upsert_research_index(research_id):
    research = (
        Research.objects.select_related('area', 'company')
        .filter(pk=research_id)
        .first()
    )
    if not research:
        SearchResearchIndex.objects.filter(research_id=research_id).delete()
        return

    text = build_research_search_text(research)
    embedding = build_embedding(text)

    obj, _ = SearchResearchIndex.objects.get_or_create(research=research)
    obj.search_text = text
    obj.embedding = embedding
    obj.save(update_fields=['search_text', 'embedding', 'updated_at'])

    SearchResearchIndex.objects.filter(research=research).update(
        search_tsv=SearchVector(Value(text), config='portuguese')
    )


def reindex_all():
    for researcher_id in Researcher.objects.values_list('id_researcher', flat=True):
        upsert_researcher_index(researcher_id)
    for research_id in Research.objects.values_list('id_research', flat=True):
        upsert_research_index(research_id)


def search_researchers(query_text, area_id=None, available=None, limit=20):
    query = (query_text or '').strip()
    if not query:
        return []

    if not SearchResearcherIndex.objects.exists():
        reindex_all()

    query_fts_text = _normalize_for_search(query)
    query_embedding_text = _with_normalized_variant(query)
    query_tokens = _tokenize(query_fts_text)
    query_token_set = set(query_tokens)
    query_vec = build_embedding(query_embedding_text)
    query_fts = SearchQuery(query_fts_text, config='portuguese', search_type='websearch')

    qs = SearchResearcherIndex.objects.select_related('researcher', 'researcher__university').annotate(
        lexical_score=SearchRank(F('search_tsv'), query_fts, normalization=32),
        semantic_distance=CosineDistance('embedding', query_vec),
    )

    if area_id is not None:
        qs = qs.filter(researcher__area__id_area=area_id)
    if available is not None:
        qs = qs.filter(researcher__availability=available)
    qs = qs.filter(researcher__status=True).distinct()

    results = []
    for item in qs[: max(limit * 3, 60)]:
        lexical = float(item.lexical_score or 0.0)
        distance = float(item.semantic_distance or 1.0)
        semantic = max(0.0, 1.0 - distance)
        item_tokens = set(_tokenize(item.search_text))
        token_coverage = 0.0
        if query_token_set:
            token_coverage = len(query_token_set & item_tokens) / float(len(query_token_set))

        # Prioriza aderencia textual da query sem perder relevancia semantica.
        hybrid = 0.45 * semantic + 0.35 * lexical + 0.20 * token_coverage

        results.append(
            {
                'id_researcher': item.researcher_id,
                'name': item.researcher.name,
                'university': item.researcher.university.name if item.researcher.university_id else None,
                'availability': item.researcher.availability,
                'score_hybrid': hybrid,
                'score_semantic': semantic,
                'score_lexical': lexical,
                'score_token_coverage': token_coverage,
            }
        )

    return _apply_relevance_cutoff(results, limit=limit)


def search_research(query_text, area_id=None, open_only=True, limit=20):
    query = (query_text or '').strip()
    if not query:
        return []

    if not SearchResearchIndex.objects.exists():
        reindex_all()

    query_fts_text = _normalize_for_search(query)
    query_embedding_text = _with_normalized_variant(query)
    query_vec = build_embedding(query_embedding_text)
    query_fts = SearchQuery(query_fts_text, config='portuguese', search_type='websearch')

    qs = SearchResearchIndex.objects.select_related('research', 'research__area', 'research__company').annotate(
        lexical_score=SearchRank(F('search_tsv'), query_fts, normalization=32),
        semantic_distance=CosineDistance('embedding', query_vec),
    )

    if area_id is not None:
        qs = qs.filter(research__area_id=area_id)
    if open_only:
        qs = qs.filter(
            Q(research__status__iexact='aberta')
            | Q(research__status__iexact='aberto')
            | Q(research__status__iexact='ativa')
            | Q(research__status__iexact='ativo')
            | Q(research__status__iexact='open')
        )

    results = []
    for item in qs[: max(limit * 3, 60)]:
        lexical = float(item.lexical_score or 0.0)
        distance = float(item.semantic_distance or 1.0)
        semantic = max(0.0, 1.0 - distance)
        hybrid = 0.65 * semantic + 0.35 * lexical

        company = item.research.company
        company_name = None
        if company:
            company_name = company.legal_name or company.name

        results.append(
            {
                'id_research': item.research_id,
                'title': item.research.title,
                'status': item.research.status,
                'area': item.research.area.name if item.research.area_id else None,
                'company': company_name,
                'score_hybrid': hybrid,
                'score_semantic': semantic,
                'score_lexical': lexical,
            }
        )

    return _apply_relevance_cutoff(results, limit=limit)

from rest_framework import permissions, response, status, views
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.search.serializers import SearchResearcherResultSerializer, SearchResearchResultSerializer
from apps.search.services import reindex_all, search_research, search_researchers
from apps.users.models import User


def _parse_limit(raw_limit):
    if raw_limit in (None, ''):
        return 20
    try:
        value = int(raw_limit)
    except ValueError:
        raise ValidationError({'limit': 'limit deve ser numero inteiro.'})
    return max(1, min(value, 50))


def _parse_bool(value):
    if value is None:
        return None
    parsed = str(value).strip().lower()
    if parsed in {'1', 'true', 'sim', 'yes'}:
        return True
    if parsed in {'0', 'false', 'nao', 'não', 'no'}:
        return False
    raise ValidationError({'available': 'available deve ser true/false.'})


def _parse_optional_int(raw_value, field_name):
    if raw_value in (None, ''):
        return None
    try:
        return int(raw_value)
    except ValueError:
        raise ValidationError({field_name: f'{field_name} deve ser numero inteiro.'})


class SearchResearchersView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.id_type != User.UserType.EMPRESA:
            raise PermissionDenied('Apenas empresas podem buscar pesquisadores.')

        query = request.query_params.get('q', '').strip()
        if not query:
            raise ValidationError({'q': 'Informe o termo de busca em q.'})

        limit = _parse_limit(request.query_params.get('limit'))
        area_id = _parse_optional_int(request.query_params.get('area_id'), 'area_id')
        available = _parse_bool(request.query_params.get('available'))

        rows = search_researchers(query_text=query, area_id=area_id, available=available, limit=limit)
        serializer = SearchResearcherResultSerializer(rows, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class SearchResearchView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.id_type != User.UserType.PESQUISADOR:
            raise PermissionDenied('Apenas pesquisadores podem buscar pesquisas.')

        query = request.query_params.get('q', '').strip()
        if not query:
            raise ValidationError({'q': 'Informe o termo de busca em q.'})

        limit = _parse_limit(request.query_params.get('limit'))
        area_id = _parse_optional_int(request.query_params.get('area_id'), 'area_id')

        open_only_raw = request.query_params.get('open_only')
        open_only = True if open_only_raw is None else _parse_bool(open_only_raw)

        rows = search_research(query_text=query, area_id=area_id, open_only=open_only, limit=limit)
        serializer = SearchResearchResultSerializer(rows, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class SearchReindexView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if not user.is_staff and not user.is_superuser:
            raise PermissionDenied('Apenas admin pode reindexar busca global.')

        reindex_all()
        return response.Response({'detail': 'Reindexacao concluida.'}, status=status.HTTP_200_OK)

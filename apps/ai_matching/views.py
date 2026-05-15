from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import MatchingProfile, Match, MatchingHistory
from .serializers import (
    MatchingProfileSerializer,
    MatchSerializer,
    MatchingHistorySerializer,
    SmartSearchRequestSerializer,
    SmartSearchResponseSerializer,
)
from .services.gemini_service import GeminiMatchingService
from apps.researchers.models import Researcher
from apps.companies.models import Company


class MatchingProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar perfis de matching.
    Usuários podem criar e atualizar seus perfis de preferências para matching.
    """
    serializer_class = MatchingProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Cada usuário só vê seu próprio perfil"""
        return MatchingProfile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Associa o perfil ao usuário atual"""
        serializer.save(user=self.request.user)


class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar matches criados.
    Os matches são criados através do processo automático de matching.
    """
    serializer_class = MatchSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        """
        Filtra matches baseado no tipo de usuário:
        - Pesquisadores veem matches onde são o pesquisador
        - Empresas veem matches onde são a empresa
        """
        user = self.request.user
        
        # Tenta encontrar se o usuário é pesquisador ou empresa
        try:
            researcher = Researcher.objects.get(user=user)
            return Match.objects.filter(researcher=researcher)
        except Researcher.DoesNotExist:
            pass
        
        try:
            company = Company.objects.get(user=user)
            return Match.objects.filter(company=company)
        except Company.DoesNotExist:
            pass
        
        return Match.objects.none()
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Aceita um match"""
        match = self.get_object()
        match.status = 'accepted'
        match.save()
        serializer = self.get_serializer(match)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rejeita um match"""
        match = self.get_object()
        match.status = 'rejected'
        match.save()
        serializer = self.get_serializer(match)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def contact(self, request, pk=None):
        """Marca um match como contatado"""
        match = self.get_object()
        match.status = 'contacted'
        match.save()
        serializer = self.get_serializer(match)
        return Response(serializer.data)


class SmartSearchViewSet(viewsets.ViewSet):
    """
    ViewSet para realizar buscas inteligentes com IA.
    Permite pesquisadores ou empresas buscar por potenciais parceiros.
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """
        Realiza uma busca inteligente.
        
        Body:
        {
            "query": "Procuro pesquisadores com expertise em machine learning",
            "search_type": "researcher",  # ou "company"
            "limit": 10,
            "threshold": 0.6
        }
        """
        serializer = SmartSearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        query_data = serializer.validated_data
        search_query = query_data['query']
        search_type = query_data['search_type']
        limit = query_data['limit']
        threshold = query_data['threshold']
        
        try:
            # Busca candidatos no banco
            if search_type == 'researcher':
                candidates = self._get_researcher_candidates()
            else:
                candidates = self._get_company_candidates()
            
            # Chama o serviço de IA
            gemini_service = GeminiMatchingService()
            results = gemini_service.smart_search(
                search_query=search_query,
                search_type=search_type,
                candidates=candidates,
                limit=limit,
                threshold=threshold
            )
            
            # Salva no histórico
            MatchingHistory.objects.create(
                user=request.user,
                search_query=search_query,
                query_type='find_researchers' if search_type == 'researcher' else 'find_companies',
                results_count=len(results.get('matches', [])),
                ai_response=results
            )
            
            return Response({
                'query': search_query,
                'search_type': search_type,
                'results': results,
                'timestamp': MatchingHistory.objects.latest('created_at').created_at
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_researcher_candidates(self) -> list:
        """Obtém lista de pesquisadores para busca"""
        researchers = Researcher.objects.filter(
            status=True,
            availability=True
        ).select_related('university').prefetch_related('area', 'resume')
        
        candidates = []
        for researcher in researchers:
            areas = ', '.join([area.name for area in researcher.area.all()]) if researcher.area.exists() else 'N/A'
            candidates.append({
                'id': researcher.id_researcher,
                'name': researcher.name,
                'description': f"Pesquisador da {researcher.university.name}, áreas: {areas}",
                'info': f"Disponível: {researcher.availability}, Status: {'Ativo' if researcher.status else 'Inativo'}"
            })
        
        return candidates
    
    def _get_company_candidates(self) -> list:
        """Obtém lista de empresas para busca"""
        companies = Company.objects.filter(status=True)
        
        candidates = []
        for company in companies:
            description = f"{company.legal_name or company.name} - {company.city}, {company.state}"
            candidates.append({
                'id': company.id_company,
                'name': company.legal_name or company.name,
                'description': description,
                'info': f"CNPJ: {company.cnpj}, Setor: {company.neighborhood}"
            })
        
        return candidates
    
    @action(detail=False, methods=['post'])
    def match_researcher_to_companies(self, request):
        """
        Encontra as melhores empresas para um pesquisador.
        
        Body:
        {
            "researcher_id": 1,
            "limit": 5
        }
        """
        researcher_id = request.data.get('researcher_id')
        limit = request.data.get('limit', 5)
        
        researcher = get_object_or_404(Researcher, id_researcher=researcher_id)
        
        # Coleta informações do pesquisador
        research_areas = list(researcher.area.values_list('name', flat=True))
        skills = list(researcher.resume.skills.values_list('name', flat=True)) if researcher.resume else []
        
        # Obtém empresas disponíveis
        companies = Company.objects.filter(status=True)
        companies_data = [
            {
                'id': c.id_company,
                'name': c.legal_name or c.name,
                'sector': c.city,
                'description': f"{c.legal_name or c.name} - {c.city}, {c.state}"
            }
            for c in companies
        ]
        
        # Chama IA para matching
        gemini_service = GeminiMatchingService()
        results = gemini_service.analyze_researcher_for_companies(
            researcher_name=researcher.name,
            university=researcher.university.name,
            research_areas=research_areas,
            experience_summary=f"Pesquisador em {', '.join(research_areas)}",
            skills=skills,
            available_companies=companies_data,
            limit=limit
        )
        
        # Salva matches no banco
        matches_created = []
        for match_data in results.get('matches', []):
            company_idx = match_data.get('company_index')
            if company_idx < len(companies):
                company = companies[company_idx]
                match_obj, created = Match.objects.update_or_create(
                    researcher=researcher,
                    company=company,
                    defaults={
                        'compatibility_score': match_data.get('compatibility_score', 0),
                        'match_reason': match_data.get('reason', ''),
                        'ai_analysis': match_data,
                    }
                )
                matches_created.append(match_obj)
        
        serializer = MatchSerializer(matches_created, many=True)
        return Response({
            'researcher': researcher.name,
            'matches': serializer.data,
            'summary': results.get('summary'),
            'insights': results.get('insights')
        })
    
    @action(detail=False, methods=['post'])
    def match_company_to_researchers(self, request):
        """
        Encontra os melhores pesquisadores para uma empresa.
        
        Body:
        {
            "company_id": 1,
            "limit": 5
        }
        """
        company_id = request.data.get('company_id')
        limit = request.data.get('limit', 5)
        
        company = get_object_or_404(Company, id_company=company_id)
        
        # Obtém pesquisadores disponíveis
        researchers = Researcher.objects.filter(
            status=True,
            availability=True
        ).select_related('university').prefetch_related('area', 'resume')
        
        researchers_data = [
            {
                'id': r.id_researcher,
                'name': r.name,
                'university': r.university.name,
                'areas': ', '.join([a.name for a in r.area.all()]) or 'N/A',
                'skills': ', '.join(list(r.resume.skills.values_list('name', flat=True))) if r.resume else 'N/A',
            }
            for r in researchers
        ]
        
        # Chama IA para matching
        gemini_service = GeminiMatchingService()
        results = gemini_service.analyze_company_for_researchers(
            company_name=company.legal_name or company.name,
            company_description=f"{company.city}, {company.state}",
            company_sector=company.neighborhood or 'N/A',
            needs="Busca por pesquisadores para colaboração",
            available_researchers=researchers_data,
            limit=limit
        )
        
        # Salva matches no banco
        matches_created = []
        for match_data in results.get('matches', []):
            researcher_idx = match_data.get('researcher_index')
            if researcher_idx < len(researchers):
                researcher = researchers[researcher_idx]
                match_obj, created = Match.objects.update_or_create(
                    researcher=researcher,
                    company=company,
                    defaults={
                        'compatibility_score': match_data.get('compatibility_score', 0),
                        'match_reason': match_data.get('reason', ''),
                        'ai_analysis': match_data,
                    }
                )
                matches_created.append(match_obj)
        
        serializer = MatchSerializer(matches_created, many=True)
        return Response({
            'company': company.legal_name or company.name,
            'matches': serializer.data,
            'summary': results.get('summary'),
            'insights': results.get('insights')
        })

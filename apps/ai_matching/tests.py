from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from apps.universities.models import University
from apps.researchers.models import Researcher
from apps.companies.models import Company
from .models import MatchingProfile, Match
import json


class MatchingProfileTestCase(TestCase):
    """Testes para o modelo MatchingProfile"""
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'password')
        self.university = University.objects.create(
            name='Test University',
            domain='test.edu'
        )
        self.researcher = Researcher.objects.create(
            name='Test Researcher',
            university=self.university
        )
    
    def test_create_researcher_matching_profile(self):
        profile = MatchingProfile.objects.create(
            user=self.user,
            profile_type='researcher',
            researcher=self.researcher,
            description='Looking for AI companies',
            keywords='machine learning, artificial intelligence, deep learning'
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.profile_type, 'researcher')
        self.assertEqual(profile.researcher, self.researcher)


class MatchTestCase(TestCase):
    """Testes para o modelo Match"""
    
    def setUp(self):
        self.university = University.objects.create(
            name='Test University',
            domain='test.edu'
        )
        self.researcher = Researcher.objects.create(
            name='Test Researcher',
            university=self.university
        )
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='12345678901234'
        )
    
    def test_create_match(self):
        match = Match.objects.create(
            researcher=self.researcher,
            company=self.company,
            compatibility_score=85.5,
            match_reason='Great match due to AI expertise'
        )
        
        self.assertEqual(match.researcher, self.researcher)
        self.assertEqual(match.company, self.company)
        self.assertEqual(match.compatibility_score, 85.5)
        self.assertEqual(match.status, 'pending')


class SmartSearchAPITestCase(APITestCase):
    """Testes para os endpoints de busca inteligente"""
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'password')
        self.token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_smart_search_endpoint_requires_auth(self):
        """Testa se o endpoint requer autenticação"""
        self.client.credentials()
        response = self.client.post('/api/ai_matching/search/search/', {
            'query': 'test',
            'search_type': 'researcher'
        })
        self.assertEqual(response.status_code, 401)
    
    def test_smart_search_invalid_request(self):
        """Testa validação de request"""
        response = self.client.post('/api/ai_matching/search/search/', {
            'query': '',  # Query vazia
            'search_type': 'invalid_type'
        })
        self.assertEqual(response.status_code, 400)

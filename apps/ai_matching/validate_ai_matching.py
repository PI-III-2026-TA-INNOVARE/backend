#!/usr/bin/env python
"""
Script de validação e teste do módulo AI Matching.

Executa bateria de testes para verificar se tudo está funcionando corretamente.

Uso:
    python validate_ai_matching.py
    ou
    python manage.py shell < validate_ai_matching.py
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

from django.contrib.auth.models import User
from apps.universities.models import University
from apps.researchers.models import Researcher
from apps.research_area.models import ResearchArea
from apps.companies.models import Company
from apps.ai_matching.models import MatchingProfile, Match, MatchingHistory
from apps.ai_matching.services.gemini_service import GeminiMatchingService


class AIMatchingValidator:
    """Classe para validar a instalação e funcionamento do AI Matching"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def test(self, name, func):
        """Decorator para executar testes"""
        print(f"\n🔍 Teste: {name}")
        print("-" * 60)
        try:
            result = func()
            if result:
                print(f"✅ PASSOU")
                self.passed += 1
            else:
                print(f"❌ FALHOU")
                self.failed += 1
        except Exception as e:
            print(f"⚠️  ERRO: {str(e)}")
            self.failed += 1
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("\n" + "="*60)
        print("🚀 VALIDAÇÃO DO MÓDULO AI MATCHING")
        print("="*60)
        
        # Testes 1: Verificações de Ambiente
        print("\n\n📋 TESTES DE AMBIENTE")
        print("="*60)
        self._test_imports()
        self._test_gemini_api_key()
        self._test_database_tables()
        
        # Testes 2: Models e Database
        print("\n\n💾 TESTES DE MODELS E BANCO DE DADOS")
        print("="*60)
        self._test_create_matching_profile()
        self._test_create_match()
        self._test_matching_history()
        
        # Testes 3: Serviço Gemini
        print("\n\n🤖 TESTES DO SERVIÇO GEMINI")
        print("="*60)
        self._test_gemini_service_initialization()
        self._test_json_parsing()
        
        # Relatório Final
        self._print_report()
    
    def _test_imports(self):
        """Testa se todos os módulos podem ser importados"""
        def test():
            from apps.ai_matching.models import MatchingProfile, Match, MatchingHistory
            from apps.ai_matching.services.gemini_service import GeminiMatchingService
            from apps.ai_matching.serializers import MatchingProfileSerializer, MatchSerializer
            from apps.ai_matching.views import MatchingProfileViewSet, SmartSearchViewSet
            return True
        
        self.test("Importação de módulos", test)
    
    def _test_gemini_api_key(self):
        """Testa se GEMINI_API_KEY está configurada"""
        def test():
            api_key = getattr(settings, 'GEMINI_API_KEY', None)
            if api_key is None:
                print("   ⚠️  GEMINI_API_KEY não configurada no .env")
                print("   Instruções: Configure a variável GEMINI_API_KEY com sua chave do Google Gemini")
                self.warnings += 1
                return True  # Não é erro fatal
            elif api_key == 'seu_api_key_aqui':
                print("   ⚠️  GEMINI_API_KEY ainda com valor exemplo")
                self.warnings += 1
                return False
            else:
                print("   ✓ GEMINI_API_KEY configurada")
                return True
        
        self.test("GEMINI_API_KEY configurada", test)
    
    def _test_database_tables(self):
        """Testa se as tabelas do banco foram criadas"""
        def test():
            from django.db import connection
            cursor = connection.cursor()
            
            tables = ['perfil_matching', 'matching', 'historico_matching']
            for table in tables:
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """)
                exists = cursor.fetchone()[0]
                print(f"   {'✓' if exists else '✗'} Tabela {table}: {'Encontrada' if exists else 'NÃO encontrada'}")
                if not exists:
                    return False
            
            cursor.close()
            return True
        
        self.test("Tabelas do banco de dados criadas", test)
    
    def _test_create_matching_profile(self):
        """Testa criação de MatchingProfile"""
        def test():
            # Limpar dados de teste anteriores
            MatchingProfile.objects.filter(
                user__username__startswith='test_'
            ).delete()
            User.objects.filter(username__startswith='test_').delete()
            
            # Criar usuário teste
            user = User.objects.create_user(
                'test_usuario',
                'test@example.com',
                'password123'
            )
            
            # Criar perfil
            profile = MatchingProfile.objects.create(
                user=user,
                profile_type='researcher',
                description='Test description',
                keywords='test, keywords'
            )
            
            print(f"   ✓ MatchingProfile criado: {profile}")
            profile.delete()
            user.delete()
            return True
        
        self.test("Criar MatchingProfile", test)
    
    def _test_create_match(self):
        """Testa criação de Match"""
        def test():
            # Limpar dados anteriores
            Match.objects.all().delete()
            Researcher.objects.filter(name__startswith='Test').delete()
            Company.objects.filter(name__startswith='Test').delete()
            University.objects.filter(name__startswith='Test').delete()
            
            # Criar dependências
            university = University.objects.create(
                name='Test University',
                domain='test.edu'
            )
            
            researcher = Researcher.objects.create(
                name='Test Researcher',
                university=university
            )
            
            company = Company.objects.create(
                name='Test Company',
                cnpj='12345678901234'
            )
            
            # Criar match
            match = Match.objects.create(
                researcher=researcher,
                company=company,
                compatibility_score=85.5,
                match_reason='Test match'
            )
            
            print(f"   ✓ Match criado: {match}")
            
            # Limpeza
            match.delete()
            company.delete()
            researcher.delete()
            university.delete()
            
            return True
        
        self.test("Criar Match", test)
    
    def _test_matching_history(self):
        """Testa criação de MatchingHistory"""
        def test():
            # Limpar dados anteriores
            MatchingHistory.objects.filter(user__username__startswith='test_').delete()
            User.objects.filter(username__startswith='test_').delete()
            
            # Criar usuário
            user = User.objects.create_user(
                'test_search_user',
                'test@example.com',
                'password123'
            )
            
            # Criar histórico
            history = MatchingHistory.objects.create(
                user=user,
                search_query='Test query',
                query_type='find_researchers',
                results_count=5,
                ai_response={'test': 'data'}
            )
            
            print(f"   ✓ MatchingHistory criado: {history}")
            
            history.delete()
            user.delete()
            
            return True
        
        self.test("Criar MatchingHistory", test)
    
    def _test_gemini_service_initialization(self):
        """Testa inicialização do serviço Gemini"""
        def test():
            try:
                service = GeminiMatchingService()
                print(f"   ✓ Serviço Gemini inicializado")
                return True
            except Exception as e:
                print(f"   ✗ Erro ao inicializar: {e}")
                return False
        
        self.test("Inicializar Serviço Gemini", test)
    
    def _test_json_parsing(self):
        """Testa parsing de JSON da resposta IA"""
        def test():
            service = GeminiMatchingService()
            
            # Teste 1: JSON válido
            json_text = '{"matches": [], "summary": "test"}'
            result = service._parse_json_response(json_text)
            assert result.get('summary') == 'test'
            print(f"   ✓ JSON válido parseado corretamente")
            
            # Teste 2: JSON dentro de texto
            json_with_text = 'Aqui está o resultado: {"matches": [1,2,3], "summary": "test2"}'
            result = service._parse_json_response(json_with_text)
            assert len(result.get('matches', [])) == 3
            print(f"   ✓ JSON dentro de texto parseado corretamente")
            
            return True
        
        self.test("Parsing de JSON", test)
    
    def _print_report(self):
        """Imprime relatório final"""
        print("\n\n" + "="*60)
        print("📊 RELATÓRIO FINAL")
        print("="*60)
        print(f"✅ Testes aprovados: {self.passed}")
        print(f"❌ Testes falhados: {self.failed}")
        print(f"⚠️  Avisos: {self.warnings}")
        
        total = self.passed + self.failed
        if total == 0:
            status = "❓ Nenhum teste executado"
        elif self.failed == 0:
            status = "✅ TODOS OS TESTES PASSARAM!"
        else:
            status = f"❌ {self.failed} teste(s) falhado(s)"
        
        print(f"\nStatus: {status}")
        
        # Recomendações
        if self.warnings > 0:
            print(f"\n⚠️  AVISOS IMPORTANTES:")
            if 'GEMINI_API_KEY' not in str(settings.GEMINI_API_KEY):
                print("   • Configure GEMINI_API_KEY no arquivo .env")
                print("     Instrução: https://aistudio.google.com/app/apikey")
        
        print("\n" + "="*60)
        
        return self.failed == 0


def run_validation():
    """Função principal para executar validação"""
    validator = AIMatchingValidator()
    success = validator.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    run_validation()

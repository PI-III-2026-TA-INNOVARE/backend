import json
import logging
from typing import List, Dict, Any
from django.conf import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiMatchingService:
    """
    Serviço que utiliza a API do Google Gemini para fazer matching inteligente
    entre pesquisadores e empresas.
    """
    
    def __init__(self):
        """Inicializa o serviço com a chave da API do Gemini"""
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            logger.warning(
                "GEMINI_API_KEY não configurada. Configure em .env ou settings.py"
            )
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def analyze_researcher_for_companies(
        self,
        researcher_name: str,
        university: str,
        research_areas: List[str],
        experience_summary: str,
        skills: List[str],
        available_companies: List[Dict[str, str]],
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Analisa um pesquisador e encontra as melhores empresas para colaboração.
        
        Args:
            researcher_name: Nome do pesquisador
            university: Universidade do pesquisador
            research_areas: Áreas de pesquisa
            experience_summary: Resumo de experiências
            skills: Habilidades do pesquisador
            available_companies: Lista de empresas disponíveis com descrição
            limit: Número máximo de matches
            
        Returns:
            Dict com matches, scores e análise
        """
        companies_text = self._format_companies_for_analysis(available_companies)
        
        prompt = f"""
Você é um especialista em matching entre pesquisadores e empresas.
Analise o pesquisador abaixo e encontre as {limit} melhores empresas para colaboração.

PESQUISADOR:
Nome: {researcher_name}
Universidade: {university}
Áreas de Pesquisa: {', '.join(research_areas)}
Experiências: {experience_summary}
Habilidades: {', '.join(skills)}

EMPRESAS DISPONÍVEIS:
{companies_text}

Tarefa:
1. Analise a compatibilidade entre o pesquisador e cada empresa
2. Retorne um JSON com os seguintes campos:
   - matches: array de objetos com:
     - company_index: índice da empresa
     - company_name: nome da empresa
     - compatibility_score: score de 0-100
     - reason: por que este é um bom match
   - summary: resumo da análise em 1-2 linhas
   - insights: insights sobre oportunidades de colaboração

Retorne APENAS um JSON válido, sem explicações adicionais.
"""
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            return result
        except Exception as e:
            logger.error(f"Erro ao analisar pesquisador: {e}")
            return {
                "matches": [],
                "summary": "Erro na análise",
                "insights": {"error": str(e)}
            }
    
    def analyze_company_for_researchers(
        self,
        company_name: str,
        company_description: str,
        company_sector: str,
        needs: str,
        available_researchers: List[Dict[str, str]],
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Analisa uma empresa e encontra os melhores pesquisadores para colaboração.
        
        Args:
            company_name: Nome da empresa
            company_description: Descrição da empresa
            company_sector: Setor/indústria
            needs: Necessidades/desafios da empresa
            available_researchers: Lista de pesquisadores com informações
            limit: Número máximo de matches
            
        Returns:
            Dict com matches, scores e análise
        """
        researchers_text = self._format_researchers_for_analysis(available_researchers)
        
        prompt = f"""
Você é um especialista em matching entre empresas e pesquisadores.
Analise a empresa abaixo e encontre os {limit} melhores pesquisadores para colaboração.

EMPRESA:
Nome: {company_name}
Descrição: {company_description}
Setor: {company_sector}
Necessidades/Desafios: {needs}

PESQUISADORES DISPONÍVEIS:
{researchers_text}

Tarefa:
1. Analise a compatibilidade entre a empresa e cada pesquisador
2. Considere: expertise, experiência, habilidades técnicas
3. Retorne um JSON com os seguintes campos:
   - matches: array de objetos com:
     - researcher_index: índice do pesquisador
     - researcher_name: nome do pesquisador
     - compatibility_score: score de 0-100
     - reason: por que este é um bom match
   - summary: resumo da análise em 1-2 linhas
   - insights: insights sobre oportunidades de colaboração

Retorne APENAS um JSON válido, sem explicações adicionais.
"""
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            return result
        except Exception as e:
            logger.error(f"Erro ao analisar empresa: {e}")
            return {
                "matches": [],
                "summary": "Erro na análise",
                "insights": {"error": str(e)}
            }
    
    def smart_search(
        self,
        search_query: str,
        search_type: str,
        candidates: List[Dict[str, str]],
        limit: int = 10,
        threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        Realiza uma busca inteligente com base em texto livre.
        
        Args:
            search_query: Query em texto livre
            search_type: 'researcher' ou 'company'
            candidates: Lista de candidatos para filtrar
            limit: Número máximo de resultados
            threshold: Score mínimo (0-1)
            
        Returns:
            Dict com resultados e análise
        """
        candidates_text = self._format_candidates_for_search(candidates, search_type)
        type_label = "pesquisadores" if search_type == "researcher" else "empresas"
        
        prompt = f"""
Você é um especialista em busca inteligente e matching.
Analise a query abaixo e encontre os {limit} melhores {type_label} relacionados.

QUERY: {search_query}

CANDIDATOS DISPONÍVEIS:
{candidates_text}

Tarefa:
1. Analise a relevância de cada candidato para a query
2. Ordene por relevância e compatibilidade
3. Retorne um JSON com os seguintes campos:
   - matches: array de objetos com:
     - index: índice do candidato
     - name: nome do candidato
     - relevance_score: score de 0-100
     - match_reason: por que é relevante
   - summary: resumo dos resultados em 1-2 linhas
   - insights: insights sobre a busca e recomendações

Considere mínimo {int(threshold * 100)}% de relevância.
Retorne APENAS um JSON válido, sem explicações adicionais.
"""
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            return result
        except Exception as e:
            logger.error(f"Erro na busca inteligente: {e}")
            return {
                "matches": [],
                "summary": "Erro na busca",
                "insights": {"error": str(e)}
            }
    
    def generate_collaboration_proposal(
        self,
        researcher_name: str,
        researcher_expertise: str,
        company_name: str,
        company_needs: str
    ) -> str:
        """
        Gera uma proposta de colaboração entre pesquisador e empresa.
        
        Args:
            researcher_name: Nome do pesquisador
            researcher_expertise: Expertise do pesquisador
            company_name: Nome da empresa
            company_needs: Necessidades da empresa
            
        Returns:
            Texto da proposta gerada
        """
        prompt = f"""
Crie uma proposta de colaboração bem estruturada entre:

PESQUISADOR: {researcher_name}
Expertise: {researcher_expertise}

EMPRESA: {company_name}
Necessidades: {company_needs}

A proposta deve incluir:
1. Sinergias identificadas
2. Áreas potenciais de colaboração
3. Benefícios mútuos
4. Próximos passos sugeridos

Mantenha o tom profissional e conciso (máximo 300 palavras).
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Erro ao gerar proposta: {e}")
            return "Erro ao gerar proposta de colaboração"
    
    @staticmethod
    def _format_companies_for_analysis(companies: List[Dict[str, str]]) -> str:
        """Formata lista de empresas para análise"""
        result = ""
        for idx, company in enumerate(companies):
            result += f"""
Empresa {idx}:
Nome: {company.get('name', 'N/A')}
Setor: {company.get('sector', 'N/A')}
Descrição: {company.get('description', 'N/A')}
"""
        return result
    
    @staticmethod
    def _format_researchers_for_analysis(researchers: List[Dict[str, str]]) -> str:
        """Formata lista de pesquisadores para análise"""
        result = ""
        for idx, researcher in enumerate(researchers):
            result += f"""
Pesquisador {idx}:
Nome: {researcher.get('name', 'N/A')}
Universidade: {researcher.get('university', 'N/A')}
Áreas: {researcher.get('areas', 'N/A')}
Habilidades: {researcher.get('skills', 'N/A')}
"""
        return result
    
    @staticmethod
    def _format_candidates_for_search(candidates: List[Dict[str, str]], type_: str) -> str:
        """Formata lista de candidatos para busca"""
        result = ""
        for idx, candidate in enumerate(candidates):
            result += f"""
Candidato {idx}:
Nome: {candidate.get('name', 'N/A')}
Descrição: {candidate.get('description', 'N/A')}
Informações Adicionais: {candidate.get('info', 'N/A')}
"""
        return result
    
    @staticmethod
    def _parse_json_response(response_text: str) -> Dict[str, Any]:
        """
        Extrai JSON da resposta da IA.
        Tenta encontrar um bloco JSON válido mesmo se houver texto extra.
        """
        try:
            # Primeiro tenta parse direto
            return json.loads(response_text)
        except json.JSONDecodeError:
            try:
                # Procura por JSON entre { e }
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        logger.warning(f"Não foi possível fazer parse do JSON: {response_text[:100]}")
        return {
            "matches": [],
            "summary": "Erro ao processar resposta",
            "insights": {}
        }

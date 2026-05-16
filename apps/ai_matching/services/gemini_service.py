import json
import logging
from typing import List, Dict, Any
from django.conf import settings

# Novas importações da SDK atualizada e Pydantic
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class MatchItem(BaseModel):
    index: int = Field(description="O índice do candidato/empresa na lista fornecida")
    name: str = Field(description="Nome da empresa ou pesquisador")
    compatibility_score: int = Field(description="Score de compatibilidade de 0 a 100")
    reason: str = Field(description="Explicação detalhada do motivo deste ser um bom match")

class AnalysisResult(BaseModel):
    matches: list[MatchItem]
    summary: str = Field(description="Resumo da análise geral em 1 a 2 linhas")
    insights: str = Field(description="Insights extras sobre as oportunidades de colaboração")

class GeminiMatchingService:
    def __init__(self):
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            logger.warning("GEMINI_API_KEY não configurada. Configure em .env")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)
            
        self.model_name = 'gemini-2.5-flash' 

    def _call_gemini_with_schema(self, prompt: str, schema: BaseModel) -> Dict[str, Any]:
        """Método auxiliar interno para chamar a IA forçando a saída em JSON."""
        if not self.client:
            raise ValueError("Cliente Gemini não inicializado (falta API Key).")

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.2 
                )
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Erro na chamada da IA: {e}")
            raise e

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
        
        companies_text = self._format_candidates(available_companies)
        
        prompt = f"""
        Você é um especialista em inovação e RH.
        Analise o pesquisador e encontre as {limit} melhores empresas para colaboração.

        PESQUISADOR:
        Nome: {researcher_name}
        Universidade: {university}
        Áreas: {', '.join(research_areas)}
        Experiência: {experience_summary}
        Habilidades: {', '.join(skills)}

        EMPRESAS DISPONÍVEIS:
        {companies_text}
        
        Sua tarefa é analisar a compatibilidade e retornar os melhores matches.
        """
        
        try:
            return self._call_gemini_with_schema(prompt, AnalysisResult)
        except Exception as e:
            return {"matches": [], "summary": "Erro na análise", "insights": str(e)}

    def analyze_company_for_researchers(
        self,
        company_name: str,
        company_description: str,
        company_sector: str,
        needs: str,
        available_researchers: List[Dict[str, str]],
        limit: int = 5
    ) -> Dict[str, Any]:
        
        researchers_text = self._format_candidates(available_researchers)
        
        prompt = f"""
        Você é um especialista em inovação tecnológica.
        Analise a empresa e encontre os {limit} melhores pesquisadores para resolver seus desafios.

        EMPRESA:
        Nome: {company_name}
        Descrição: {company_description}
        Setor: {company_sector}
        Necessidades: {needs}

        PESQUISADORES DISPONÍVEIS:
        {researchers_text}
        
        Analise a compatibilidade técnica e retorne os melhores matches.
        """
        
        try:
            return self._call_gemini_with_schema(prompt, AnalysisResult)
        except Exception as e:
            return {"matches": [], "summary": "Erro na análise", "insights": str(e)}

    @staticmethod
    def _format_candidates(candidates: List[Dict[str, str]]) -> str:
        result = []
        for idx, candidate in enumerate(candidates):
            info = "\n".join([f"  {k.capitalize()}: {v}" for k, v in candidate.items()])
            result.append(f"Índice {idx}:\n{info}")
        return "\n\n".join(result)
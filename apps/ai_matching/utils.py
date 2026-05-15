"""
Utilitários para o módulo AI Matching.

Este arquivo contém funções auxiliares para:
- Normalização de texto
- Cálculo de similaridade
- Parsing de dados
- Cache de resultados
"""

import hashlib
import json
from typing import Dict, List, Any
from functools import lru_cache


class TextNormalizer:
    """Normaliza e processa texto para matching"""
    
    @staticmethod
    def normalize(text: str) -> str:
        """
        Normaliza texto removendo caracteres especiais e espaços extras.
        
        Args:
            text: Texto a normalizar
            
        Returns:
            Texto normalizado em minúsculas
        """
        if not text:
            return ""
        
        # Converter para minúsculas
        text = text.lower()
        
        # Remover acentos (simplificado)
        import unicodedata
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        
        # Remover caracteres especiais
        text = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in text)
        
        # Remover espaços múltiplos
        text = ' '.join(text.split())
        
        return text
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 3) -> List[str]:
        """
        Extrai palavras-chave de um texto.
        
        Args:
            text: Texto para extrair keywords
            min_length: Tamanho mínimo da palavra
            
        Returns:
            Lista de palavras-chave
        """
        normalized = TextNormalizer.normalize(text)
        words = normalized.split()
        
        # Remover palavras muito curtas e stopwords comuns
        stopwords = {
            'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas',
            'e', 'ou', 'mas', 'de', 'do', 'da', 'em', 'para',
            'por', 'com', 'sem', 'que', 'qual', 'quais',
        }
        
        keywords = [
            w for w in words
            if len(w) >= min_length and w not in stopwords
        ]
        
        # Remover duplicatas mantendo ordem
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:20]  # Limitar a 20 keywords


class SimilarityCalculator:
    """Calcula similaridade entre textos"""
    
    @staticmethod
    def jaccard_similarity(text1: str, text2: str) -> float:
        """
        Calcula similaridade de Jaccard entre dois textos.
        
        Score: 0 (completamente diferentes) a 1 (idênticos)
        
        Args:
            text1: Primeiro texto
            text2: Segundo texto
            
        Returns:
            Score de similaridade entre 0 e 1
        """
        keywords1 = set(TextNormalizer.extract_keywords(text1))
        keywords2 = set(TextNormalizer.extract_keywords(text2))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def overlap_similarity(text1: str, text2: str) -> float:
        """
        Calcula similaridade de sobreposição.
        
        Args:
            text1: Primeiro texto
            text2: Segundo texto
            
        Returns:
            Score entre 0 e 1
        """
        keywords1 = set(TextNormalizer.extract_keywords(text1))
        keywords2 = set(TextNormalizer.extract_keywords(text2))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        min_len = min(len(keywords1), len(keywords2))
        overlap = len(keywords1 & keywords2)
        
        return overlap / min_len if min_len > 0 else 0.0


class ResponseCache:
    """Cache simples para respostas da IA"""
    
    _cache = {}
    _max_size = 100
    
    @classmethod
    def get_key(cls, query: str, search_type: str) -> str:
        """Gera chave de cache"""
        content = f"{query}:{search_type}"
        return hashlib.md5(content.encode()).hexdigest()
    
    @classmethod
    def get(cls, query: str, search_type: str) -> Dict[str, Any] | None:
        """
        Recupera resposta do cache.
        
        Args:
            query: Query da busca
            search_type: Tipo de busca
            
        Returns:
            Resposta cacheada ou None
        """
        key = cls.get_key(query, search_type)
        return cls._cache.get(key)
    
    @classmethod
    def set(cls, query: str, search_type: str, response: Dict[str, Any]) -> None:
        """
        Armazena resposta em cache.
        
        Args:
            query: Query da busca
            search_type: Tipo de busca
            response: Resposta a cachear
        """
        if len(cls._cache) >= cls._max_size:
            # Remove item mais antigo (FIFO)
            print("⚠️  Cache cheio, removendo itens antigos")
            cls._cache.popitem()
        
        key = cls.get_key(query, search_type)
        cls._cache[key] = response
    
    @classmethod
    def clear(cls) -> None:
        """Limpa todo o cache"""
        cls._cache.clear()
    
    @classmethod
    def size(cls) -> int:
        """Retorna tamanho do cache"""
        return len(cls._cache)


class DataValidator:
    """Valida dados de entrada"""
    
    @staticmethod
    def validate_match_data(data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Valida dados de match.
        
        Args:
            data: Dados a validar
            
        Returns:
            Tuple (is_valid, message)
        """
        required_fields = ['researcher_id', 'company_id', 'compatibility_score']
        
        for field in required_fields:
            if field not in data:
                return False, f"Campo obrigatório faltando: {field}"
        
        score = data.get('compatibility_score')
        if not isinstance(score, (int, float)) or not 0 <= score <= 100:
            return False, "compatibility_score deve estar entre 0 e 100"
        
        return True, "Dados válidos"
    
    @staticmethod
    def validate_search_query(query: str, min_length: int = 5) -> tuple[bool, str]:
        """
        Valida query de busca.
        
        Args:
            query: Query a validar
            min_length: Comprimento mínimo
            
        Returns:
            Tuple (is_valid, message)
        """
        if not query or not isinstance(query, str):
            return False, "Query deve ser uma string não vazia"
        
        if len(query.strip()) < min_length:
            return False, f"Query deve ter pelo menos {min_length} caracteres"
        
        return True, "Query válida"


class JSONHelper:
    """Auxiliares para JSON"""
    
    @staticmethod
    def safe_json_loads(json_str: str, default: Any = None) -> Any:
        """
        Carrega JSON com fallback para default se erro.
        
        Args:
            json_str: String JSON
            default: Valor padrão se erro
            
        Returns:
            Objeto Python ou default
        """
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return default
    
    @staticmethod
    def safe_json_dumps(obj: Any, default: str = "{}") -> str:
        """
        Converte para JSON com fallback.
        
        Args:
            obj: Objeto a converter
            default: String padrão se erro
            
        Returns:
            String JSON ou default
        """
        try:
            return json.dumps(obj, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return default


# Exemplo de uso
if __name__ == "__main__":
    print("="*60)
    print("FERRAMENTAS DE UTILITÁRIO - AI MATCHING")
    print("="*60)
    
    # Teste 1: Normalização
    print("\n1️⃣  Normalização de Texto:")
    text = "Procuro PESQUISADORES com Expertise em Machine Learning!!"
    normalized = TextNormalizer.normalize(text)
    print(f"Original:   {text}")
    print(f"Normalizado: {normalized}")
    
    # Teste 2: Keywords
    print("\n2️⃣  Extração de Keywords:")
    keywords = TextNormalizer.extract_keywords(text)
    print(f"Keywords: {keywords}")
    
    # Teste 3: Similaridade
    print("\n3️⃣  Cálculo de Similaridade:")
    text1 = "Python machine learning deep learning"
    text2 = "Deep learning AI python"
    similarity = SimilarityCalculator.jaccard_similarity(text1, text2)
    print(f"Texto 1: {text1}")
    print(f"Texto 2: {text2}")
    print(f"Similaridade Jaccard: {similarity:.2%}")
    
    # Teste 4: Cache
    print("\n4️⃣  Cache de Respostas:")
    query = "pesquisadores machine learning"
    response = {"matches": [1, 2, 3]}
    ResponseCache.set(query, "researcher", response)
    cached = ResponseCache.get(query, "researcher")
    print(f"Cacheado: {cached}")
    print(f"Tamanho cache: {ResponseCache.size()}")
    
    # Teste 5: Validação
    print("\n5️⃣  Validação de Dados:")
    match_data = {
        "researcher_id": 1,
        "company_id": 2,
        "compatibility_score": 85
    }
    is_valid, message = DataValidator.validate_match_data(match_data)
    print(f"Match data válido: {is_valid} - {message}")

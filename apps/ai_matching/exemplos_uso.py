"""
EXEMPLOS DE USO - MODULE AI MATCHING

Este arquivo contém exemplos práticos de como usar o módulo ai_matching
com requisições HTTP, Python e análises de resposta.
"""

# ============================================================================
# 1. SETUP INICIAL - Obter Token JWT
# ============================================================================

"""
Primeiro, você precisa se autenticar e obter um JWT token.

Endpoint: POST /api/token/
Body:
{
    "username": "seu_usuario",
    "password": "sua_senha"
}

Resposta:
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

Use o valor de "access" como seu TOKEN nos exemplos abaixo.
"""

# ============================================================================
# 2. EXEMPLOS COM PYTHON - Usando Requests
# ============================================================================

import requests
import json

# Configurações
BASE_URL = "http://localhost:8000/api/ai_matching"
TOKEN = "seu_jwt_token_aqui"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# ============================================================================
# 2.1 CRIAR PERFIL DE MATCHING - Pesquisador
# ============================================================================

def create_researcher_profile():
    """
    Cria um perfil de matching para um pesquisador.
    """
    data = {
        "profile_type": "researcher",
        "description": """
        Sou pesquisador com 5+ anos de experiência em Machine Learning 
        e Inteligência Artificial. Tenho expertise em deep learning, 
        processamento de linguagem natural (NLP) e visão computacional. 
        Procuro colaborar com empresas que trabalhem em transformação digital 
        e inovação tecnológica.
        """,
        "keywords": "machine learning, deep learning, NLP, computer vision, Python, TensorFlow, PyTorch"
    }
    
    response = requests.post(
        f"{BASE_URL}/profiles/",
        headers=headers,
        json=data
    )
    
    print("Status:", response.status_code)
    print("Resposta:", json.dumps(response.json(), indent=2, ensure_ascii=False))
    return response.json()


# ============================================================================
# 2.2 CRIAR PERFIL DE MATCHING - Empresa
# ============================================================================

def create_company_profile():
    """
    Cria um perfil de matching para uma empresa.
    """
    data = {
        "profile_type": "company",
        "description": """
        Somos uma startup de fintech focada em transformação digital. 
        Procuramos pesquisadores para colaborar em projetos de:
        - Detecção de fraude com ML
        - Análise de riscos com IA
        - Otimização de processos
        """,
        "keywords": "fintech, machine learning, detecção fraude, IA, análise dados"
    }
    
    response = requests.post(
        f"{BASE_URL}/profiles/",
        headers=headers,
        json=data
    )
    
    print("Status:", response.status_code)
    print("Resposta:", json.dumps(response.json(), indent=2, ensure_ascii=False))
    return response.json()


# ============================================================================
# 2.3 BUSCA INTELIGENTE - Pesquisador buscando empresas
# ============================================================================

def smart_search_companies():
    """
    Um pesquisador faz uma busca inteligente por empresas.
    """
    data = {
        "query": """
        Procuro trabalhar com empresas de tecnologia que estejam 
        investindo em IA e machine learning. Prefiro startups ou 
        empresas em fase de transformação digital que valorizem inovação.
        Tenho experiência em processamento de dados em larga escala.
        """,
        "search_type": "company",
        "limit": 5,
        "threshold": 0.65
    }
    
    response = requests.post(
        f"{BASE_URL}/search/search/",
        headers=headers,
        json=data
    )
    
    print("Status:", response.status_code)
    print("Resposta:", json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # Processando resultados
    if response.status_code == 200:
        data = response.json()
        print("\n📊 ANÁLISE DA BUSCA:")
        print(f"Query: {data['query']}")
        print(f"Tipo: {data['search_type']}")
        print(f"\nResumo: {data['results']['summary']}")
        print(f"\nMatches encontrados: {len(data['results']['matches'])}")
        
        for match in data['results']['matches']:
            print(f"\n✅ {match.get('company_name')}")
            print(f"   Score: {match.get('compatibility_score')}%")
            print(f"   Motivo: {match.get('match_reason')}")


# ============================================================================
# 2.4 BUSCA INTELIGENTE - Empresa buscando pesquisadores
# ============================================================================

def smart_search_researchers():
    """
    Uma empresa faz uma busca inteligente por pesquisadores.
    """
    data = {
        "query": """
        Procuramos pesquisadores com expertise em machine learning 
        e IA para um projeto de detecção de fraude em tempo real. 
        Preferência por profissionais com experiência em sistemas distribuídos 
        e processamento de dados em alta escala.
        """,
        "search_type": "researcher",
        "limit": 10,
        "threshold": 0.60
    }
    
    response = requests.post(
        f"{BASE_URL}/search/search/",
        headers=headers,
        json=data
    )
    
    print("Status:", response.status_code)
    print("Resposta:", json.dumps(response.json(), indent=2, ensure_ascii=False))


# ============================================================================
# 2.5 MATCHING AUTOMÁTICO - Pesquisador com Empresas
# ============================================================================

def match_researcher_to_companies(researcher_id=1):
    """
    Sistema faz matching automático entre um pesquisador e empresas disponíveis.
    A IA analisa expertise do pesquisador e necessidades das empresas.
    """
    data = {
        "researcher_id": researcher_id,
        "limit": 5
    }
    
    response = requests.post(
        f"{BASE_URL}/search/match_researcher_to_companies/",
        headers=headers,
        json=data
    )
    
    print("Status:", response.status_code)
    print("Resposta:", json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # Processando resultados
    if response.status_code == 200:
        data = response.json()
        print("\n🎯 MATCHING AUTOMÁTICO - PESQUISADOR VS EMPRESAS:")
        print(f"Pesquisador: {data['researcher']}")
        print(f"\nResumo: {data['summary']}")
        print(f"\nMatches Encontrados:")
        
        for match in data['matches']:
            print(f"\n🏢 {match['company_name']}")
            print(f"   Score de Compatibilidade: {match['compatibility_score']}%")
            print(f"   Status: {match['status_display']}")
            print(f"   Motivo: {match['match_reason']}")
            
            # Mostrar insights da IA se disponível
            if match.get('ai_analysis'):
                print(f"   Análise IA: {match['ai_analysis']}")


# ============================================================================
# 2.6 MATCHING AUTOMÁTICO - Empresa com Pesquisadores
# ============================================================================

def match_company_to_researchers(company_id=1):
    """
    Sistema faz matching automático entre uma empresa e pesquisadores disponíveis.
    """
    data = {
        "company_id": company_id,
        "limit": 5
    }
    
    response = requests.post(
        f"{BASE_URL}/search/match_company_to_researchers/",
        headers=headers,
        json=data
    )
    
    print("Status:", response.status_code)
    print("Resposta:", json.dumps(response.json(), indent=2, ensure_ascii=False))


# ============================================================================
# 2.7 GERENCIAR MATCHES - Aceitar
# ============================================================================

def accept_match(match_id=1):
    """
    Aceita um match proposto.
    """
    response = requests.post(
        f"{BASE_URL}/matches/{match_id}/accept/",
        headers=headers
    )
    
    print("Status:", response.status_code)
    print("Match aceito:", json.dumps(response.json(), indent=2, ensure_ascii=False))


# ============================================================================
# 2.8 GERENCIAR MATCHES - Rejeitar
# ============================================================================

def reject_match(match_id=1):
    """
    Rejeita um match.
    """
    response = requests.post(
        f"{BASE_URL}/matches/{match_id}/reject/",
        headers=headers
    )
    
    print("Status:", response.status_code)
    print("Match rejeitado:", json.dumps(response.json(), indent=2, ensure_ascii=False))


# ============================================================================
# 2.9 GERENCIAR MATCHES - Marcar como Contatado
# ============================================================================

def mark_as_contacted(match_id=1):
    """
    Marca um match como contatado (iniciou comunicação).
    """
    response = requests.post(
        f"{BASE_URL}/matches/{match_id}/contact/",
        headers=headers
    )
    
    print("Status:", response.status_code)
    print("Match marcado como contatado:", json.dumps(response.json(), indent=2, ensure_ascii=False))


# ============================================================================
# 2.10 LISTAR MEUS MATCHES
# ============================================================================

def list_my_matches():
    """
    Lista todos os matches do usuário autenticado.
    """
    response = requests.get(
        f"{BASE_URL}/matches/",
        headers=headers
    )
    
    print("Status:", response.status_code)
    data = response.json()
    
    print("\n📋 MEUS MATCHES:")
    print(f"Total: {data.get('count', 0)}")
    
    for match in data.get('results', []):
        print(f"\n✅ {match['researcher_name']} ↔️ {match['company_name']}")
        print(f"   Score: {match['compatibility_score']}%")
        print(f"   Status: {match['status_display']}")
        print(f"   Criado em: {match['created_at']}")


# ============================================================================
# 3. EXEMPLOS COM cURL
# ============================================================================

"""
# 1. Busca inteligente
curl -X POST http://localhost:8000/api/ai_matching/search/search/ \\
  -H "Authorization: Bearer SEU_TOKEN_JWT" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "Pesquisadores especialistas em blockchain e criptografia",
    "search_type": "researcher",
    "limit": 10,
    "threshold": 0.6
  }'

# 2. Listar matches
curl -X GET http://localhost:8000/api/ai_matching/matches/ \\
  -H "Authorization: Bearer SEU_TOKEN_JWT" \\
  -H "Content-Type: application/json"

# 3. Aceitar match
curl -X POST http://localhost:8000/api/ai_matching/matches/1/accept/ \\
  -H "Authorization: Bearer SEU_TOKEN_JWT" \\
  -H "Content-Type: application/json"

# 4. Rejeitar match
curl -X POST http://localhost:8000/api/ai_matching/matches/1/reject/ \\
  -H "Authorization: Bearer SEU_TOKEN_JWT" \\
  -H "Content-Type: application/json"

# 5. Marcar como contatado
curl -X POST http://localhost:8000/api/ai_matching/matches/1/contact/ \\
  -H "Authorization: Bearer SEU_TOKEN_JWT" \\
  -H "Content-Type: application/json"

# 6. Matching automático
curl -X POST http://localhost:8000/api/ai_matching/search/match_researcher_to_companies/ \\
  -H "Authorization: Bearer SEU_TOKEN_JWT" \\
  -H "Content-Type: application/json" \\
  -d '{
    "researcher_id": 1,
    "limit": 5
  }'
"""

# ============================================================================
# 4. FLUXO COMPLETO - Exemplo End-to-End
# ============================================================================

def complete_workflow():
    """
    Demonstra um fluxo completo de uso do sistema.
    """
    print("\n" + "="*70)
    print("FLUXO COMPLETO DE USO - AI MATCHING")
    print("="*70)
    
    # 1. Criar perfis
    print("\n1️⃣  Criando perfil de pesquisador...")
    researcher_profile = create_researcher_profile()
    
    print("\n2️⃣  Criando perfil de empresa...")
    company_profile = create_company_profile()
    
    # 2. Fazer buscas
    print("\n3️⃣  Pesquisador faz busca por empresas...")
    smart_search_companies()
    
    print("\n4️⃣  Empresa faz busca por pesquisadores...")
    smart_search_researchers()
    
    # 3. Matching automático
    print("\n5️⃣  Sistema faz matching automático...")
    match_researcher_to_companies(researcher_id=1)
    
    # 4. Gerenciar matches
    print("\n6️⃣  Listando meus matches...")
    list_my_matches()
    
    print("\n7️⃣  Aceitando um match...")
    accept_match(match_id=1)
    
    print("\n8️⃣  Marcando como contatado...")
    mark_as_contacted(match_id=1)


# ============================================================================
# 5. SCRIPT PARA TESTAR
# ============================================================================

if __name__ == "__main__":
    """
    Para executar este script:
    
    1. Configure o TOKEN com seu JWT válido
    2. Execute: python exemplos_uso.py
    
    Ou execute funções individuais:
    python -c "from exemplos_uso import *; smart_search_companies()"
    """
    
    print("""
    🚀 EXEMPLOS DE USO - AI MATCHING MODULE
    
    Funções disponíveis:
    - create_researcher_profile()
    - create_company_profile()
    - smart_search_companies()
    - smart_search_researchers()
    - match_researcher_to_companies(researcher_id)
    - match_company_to_researchers(company_id)
    - accept_match(match_id)
    - reject_match(match_id)
    - mark_as_contacted(match_id)
    - list_my_matches()
    - complete_workflow()
    
    Exemplo de uso:
    >>> from exemplos_uso import *
    >>> smart_search_companies()
    """)

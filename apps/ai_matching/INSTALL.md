# 🚀 Guia de Instalação - AI Matching Module

## 📦 Pré-requisitos

- Python 3.8+
- Django 5.0+
- PostgreSQL (já configurado do projeto)
- API Key do Google Gemini

## 🔧 Passo a Passo de Instalação

### Passo 1: Obter API Key do Google Gemini

1. Acesse [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Clique em **"Get API Key"**
3. Selecione **"Create API key in new project"** (ou projeto existente)
4. Copie a chave gerada

**Procure uma chave assim:**
```
AIzaSy...suaChaveAqui...12345
```

### Passo 2: Configurar Variáveis de Ambiente

#### 2.1 Criar/Atualizar arquivo `.env`

Na raiz do projeto, abra ou crie o arquivo `.env`:

```bash
# Adicione ou atualize:
GEMINI_API_KEY=AIzaSy...suaChaveAqui...12345
```

**Arquivo `.env` completo recomendado:**
```env
# Database
DB_NAME=seu_banco
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432

# Security
SECRET_KEY=sua_chave_secreta_super_longa_e_aleatoria_aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Google Gemini API
GEMINI_API_KEY=AIzaSy...
```

### Passo 3: Instalar Dependência do Gemini

```bash
# Instalar a biblioteca Google Generative AI
pip install google-generativeai==0.3.0

# Ou atualizar suas dependências
pip install -r requirements.txt google-generativeai==0.3.0
```

### Passo 4: Criar Migrações

```bash
# Gerar as migrações do novo app
python manage.py makemigrations ai_matching

# Verificar se as migrações foram criadas corretamente
python manage.py showmigrations ai_matching

# Executar as migrações no banco
python manage.py migrate ai_matching
```

**Esperado:**
```
Migrations for 'ai_matching':
  apps/ai_matching/migrations/0001_initial.py
    - Create model MatchingProfile
    - Create model Match
    - Create model MatchingHistory
```

### Passo 5: Verificar Instalação

```bash
# Entrar no shell Django
python manage.py shell

# Importar os modelos para verificar
from apps.ai_matching.models import MatchingProfile, Match, MatchingHistory
from apps.ai_matching.services.gemini_service import GeminiMatchingService

# Testar importação do Gemini
service = GeminiMatchingService()
print("✅ Serviço Gemini inicializado com sucesso!")

# Sair
exit()
```

### Passo 6: Iniciar o Servidor

```bash
# Iniciar o servidor Django
python manage.py runserver

# Esperado:
# Starting development server at http://127.0.0.1:8000/
# Quit the server with CONTROL-C.
```

### Passo 7: Testar API

#### 7.1 Autenticação

Primeiro, obtenha um token JWT:

```bash
# Terminal/PowerShell
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "seu_usuario", "password": "sua_senha"}'
```

Você receberá:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

Copie o valor do campo `"access"` - este é seu JWT token.

#### 7.2 Teste da Busca Inteligente

```bash
# Substituir SEU_TOKEN pelo token obtido acima

curl -X POST http://localhost:8000/api/ai_matching/search/search/ \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Pesquisadores com expertise em machine learning",
    "search_type": "researcher",
    "limit": 5,
    "threshold": 0.6
  }'
```

**Resposta esperada:**
```json
{
  "query": "Pesquisadores com...",
  "search_type": "researcher",
  "results": {
    "matches": [...],
    "summary": "Encontrados X pesquisadores relevantes...",
    "insights": {...}
  }
}
```

## 📚 Estrutura Criada

```
apps/ai_matching/
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py
├── services/
│   ├── __init__.py
│   └── gemini_service.py         # Integração com Gemini AI
├── __init__.py
├── admin.py                      # Admin Django
├── apps.py                       # Configuração do app
├── models.py                     # Models (MatchingProfile, Match, History)
├── serializers.py                # DRF Serializers
├── views.py                      # ViewSets e Endpoints
├── urls.py                       # Rotas da API
├── tests.py                      # Testes unitários
├── exemplos_uso.py               # Exemplos de código
└── README.md                     # Documentação
```

## ✅ Checklist de Configuração

- [ ] API Key do Google Gemini obtida
- [ ] `.env` configurado com `GEMINI_API_KEY`
- [ ] `google-generativeai` instalado
- [ ] Migrações criadas com `makemigrations`
- [ ] Migrações aplicadas com `migrate`
- [ ] Servidor iniciado com `runserver`
- [ ] Token JWT obtido através da API
- [ ] Teste de busca executado com sucesso
- [ ] Admin Django acessível em `/admin/`

## 🐛 Troubleshooting

### Erro: "GEMINI_API_KEY não configurada"

**Solução:**
```bash
# Verificar se .env existe
cat .env | grep GEMINI_API_KEY

# Se não encontrar, adicionar ao .env:
echo "GEMINI_API_KEY=sua_chave_aqui" >> .env

# Reiniciar servidor
```

### Erro: "ModuleNotFoundError: No module named 'google'"

**Solução:**
```bash
# Instalar:
pip install google-generativeai==0.3.0
pip install --upgrade pip
```

### Erro: "PermissionDenied na API Gemini"

**Solução:**
- Verificar se a API Key está correta
- Testar em [Google AI Studio](https://aistudio.google.com/)
- Verificar se a conta Google tem acesso à API

### Migrações não aparecem

**Solução:**
```bash
# Limpar cache
python manage.py clear_cache

# Tentar novamente
python manage.py makemigrations ai_matching
python manage.py migrate
```

### Teste retorna "connection refused"

**Solução:**
```bash
# Verificar se servidor está rodando
python manage.py runserver

# Em outro terminal, testar:
curl http://localhost:8000/api/docs/
```

## 📊 Verificar Banco de Dados

```bash
# Entrar no PostgreSQL
psql -U seu_usuario -d seu_banco

# Ver tabelas criadas
\dt schema_name.matching*

# Ver específica
SELECT * FROM perfil_matching;
SELECT * FROM matching;
SELECT * FROM historico_matching;

# Sair
\q
```

## 🔍 Admin Django

Acesse o painel administrativo:

1. URL: `http://localhost:8000/admin/`
2. Login com superuser (crie se não existir):
   ```bash
   python manage.py createsuperuser
   ```
3. Navegue para `AI Matching` seção

No admin você pode:
- ✅ Criar perfis de matching manualmente
- ✅ Visualizar todos os matches
- ✅ Ver histórico de buscas
- ✅ Mudar status de matches
- ✅ Filtrar por score ou data

## 🚀 Próximos Passos

Após instalação bem-sucedida:

1. **Criar usuários teste:**
   ```bash
   python manage.py createsuperuser
   # Criar usuário normal via API
   ```

2. **Criar dados de teste:**
   ```bash
   python manage.py shell
   # Ver exemplos_uso.py para criar perfis
   ```

3. **Usar exemplos do `exemplos_uso.py`:**
   ```bash
   python exemplos_uso.py
   ```

4. **Consultar documentação:**
   - `README.md` - Documentação completa
   - `exemplos_uso.py` - Exemplos práticos de código
   - Swagger/OpenAPI em `/api/docs/`

## 📞 Suporte

Se encontrar problemas:

1. **Verificar logs:**
   ```bash
   python manage.py runserver --verbosity 2
   ```

2. **Ver erros na API:**
   ```bash
   curl -v http://localhost:8000/api/ai_matching/search/search/
   ```

3. **Testar Gemini diretamente:**
   ```python
   import google.generativeai as genai
   genai.configure(api_key="SEU_TOKEN")
   model = genai.GenerativeModel('gemini-pro')
   response = model.generate_content("Hello!")
   print(response.text)
   ```

---

**Versão:** 1.0.0  
**Data:** 2024-01-15  
**Status:** ✅ Pronto para usar

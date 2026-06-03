# P&D Connect API

API REST para conexão entre pesquisadores e empresas, incentivando parcerias em pesquisa e desenvolvimento.

**Stack:** Django 6 · Django REST Framework · PostgreSQL · Python 3.14

---

## Requisitos

- Python 3.11+
- PostgreSQL 14+

---

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/PI-III-2026-TA-INNOVARE/backend.git
cd backend
```

### 2. Criar e ativar o ambiente virtual

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
cp .env.example .env
```

Edite o `.env`:

```env
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=
DB_USER=postgres
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
```

### 5. Criar o banco de dados

```bash
# Via psql
psql -U postgres -c "CREATE DATABASE connect_api;"

# Ou pelo pgAdmin: botão direito em Databases → Create → Database
```

### 6. Rodar as migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Iniciar o servidor

```bash
python manage.py runserver
```

A API estará disponível em: `http://127.0.0.1:8000`

### Execução assíncrona de match (opcional)

Para testar o match IA com fila assíncrona:

1. Configure no `.env`:

```env
AI_MATCH_ASYNC_ENABLED=True
REDIS_URL=redis://localhost:6379/0
```

2. Inicie o worker Celery em outro terminal:

```bash
celery -A config worker --pool=solo -l info
```

Com isso, os sinais de criação/edição enfileiram tarefas no Redis e o worker processa o match em background.

### Rerank com Gemini

Opcionalmente, você pode habilitar o reranking dos melhores candidatos gerados por pgvector + MiniLM (base semântica) com Gemini:

```env
GEMINI_API_KEY=<sua_chave>
AI_MATCH_RERANK_ENABLED=True
AI_MATCH_RERANK_TOP_N=12
AI_MATCH_RERANK_WEIGHT=0.35
AI_MATCH_GEMINI_MODEL=gemini-2.5-flash
```

Quando habilitado, o sistema combina o score da base com o score do Gemini apenas no Top-N.
Se a API do Gemini falhar, o sistema mantém automaticamente o score da base (fallback seguro).

---

## Documentação interativa

Acesse a documentação Swagger gerada automaticamente:

```
http://127.0.0.1:8000/api/docs/
```

---

## Rotas da API

Todas as rotas têm o prefixo `/api/`. A variável `{id}` representa o identificador do recurso.

Rotas marcadas com ✅ exigem o header:
```
Authorization: Bearer <access_token>
```

---

### Users (Autenticação)

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| `POST` | `/api/auth/register/` | ❌ | Criar usuário (pesquisador ou empresa) |
| `POST` | `/api/auth/token/` | ❌ | Login — retorna access e refresh token |
| `GET` | `/api/auth/profile/` | ✅ | Ver dados do usuário autenticado |

#### Criar usuário — pesquisador

```json
POST /api/auth/register/
Content-Type: application/json

{
  "email": "pesquisador@edu.br", // obrigatório e-mail institucional
  "password": "minimo8caracteres",
  "id_tipo": "pesquisador",
  "name": "Pesquisador Exemplo",
  "university": 4,
  "availability": true,
}
```

#### Criar usuário — empresa

```json
POST /api/auth/register/
Content-Type: application/json

{
  "email": "empresa@teste.com",
  "password": "minimo8caracteres",
  "id_tipo": "empresa",
  "cnpj": "10.000.000/0001-00",
}

// exemplo de campos gerados após validação do cnpj

// "empresa": {
//     "razao_social": "GOOGLE BRASIL INTERNET LTDA.",
//     "situacao_cadastral": "ATIVA",
//     "municipio": "SAO PAULO",
//     "uf": "SP",
//     "endereco": {
//         "logradouro": "BRIG FARIA LIMA",
//         "numero": "3477",
//         "complemento": "ANDAR 17A20 TSUL  2  17A20",
//         "bairro": "ITAIM BIBI",
//         "cep": "04538133"
//     }
// }
```

#### Login

```json
POST /api/auth/token/
Content-Type: application/json

{
  "email": "usuario@email.com",
  "password": "minimo8caracteres"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### Companies (Empresas)

Todos os endpoints (exceto consulta de CNPJ) requerem autenticação ✅

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/companies/` | Listar todas as empresas |
| `POST` | `/api/companies/` | Criar empresa |
| `GET` | `/api/companies/{id}` | Buscar empresa por ID |
| `PUT` | `/api/companies/{id}` | Atualizar empresa completa |
| `PATCH` | `/api/companies/{id}` | Atualizar empresa parcialmente |
| `DELETE` | `/api/companies/{id}` | Remover empresa |
| `POST` | `/api/companies/cnpj-lookup/` | Consultar dados de CNPJ |

#### Exemplo de criação

```json
POST /api/companies/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Exemplo Ltda",
  "cnpj": "00.000.000/0001-00",
  "registration_status": "Ativo",
  "status": true
}
```

---

### Researchers (Pesquisadores)

Todos os endpoints requerem autenticação ✅

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/researchers/` | Listar todos os pesquisadores |
| `POST` | `/api/researchers/` | Criar pesquisador |
| `GET` | `/api/researchers/{id}` | Buscar pesquisador por ID |
| `PUT` | `/api/researchers/{id}` | Atualizar pesquisador completo |
| `PATCH` | `/api/researchers/{id}` | Atualizar pesquisador parcialmente |
| `DELETE` | `/api/researchers/{id}` | Remover pesquisador |
| `GET` | `/api/researchers/{id}/resume/` | Buscar currículo do pesquisador |

#### Exemplo de criação

```json
POST /api/researchers/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Pesquisador Exemplo",
  "availability": true,
  "status": true,
  "university": 1,
}
```

---

### Research (Pesquisas)

Todos os endpoints requerem autenticação ✅ (Apenas usuários do tipo empresa podem criar pesquisas)

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/research/` | Listar todas as pesquisas |
| `POST` | `/api/research/` | Criar pesquisa |
| `GET` | `/api/research/{id}` | Buscar pesquisa por ID |
| `PUT` | `/api/research/{id}` | Atualizar pesquisa completa |
| `PATCH` | `/api/research/{id}` | Atualizar pesquisa parcialmente |
| `DELETE` | `/api/research/{id}` | Remover pesquisa |

#### Exemplo de criação

```json
POST /api/research/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Análise de Estabilidade de Taludes em Áreas Urbanas",
  "scope": "Estudo do comportamento de solos em encostas urbanas.",
  "goal": "Desenvolver um modelo preditivo para identificar áreas de risco.",
  "justification": "O crescimento urbano em áreas inclinadas aumenta o risco de deslizamentos.",
  "results": "Redução de riscos geotécnicos.",
  "deadline": "2026-11-15 18:00",
  "budget": 200000.00,
  "area": 10
}
```

---

### Research Area (Áreas de Pesquisa)

Todos os endpoints requerem autenticação ✅

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/research/area/` | Listar todas as áreas de pesquisa |
| `POST` | `/api/research/area/` | Criar área de pesquisa |
| `GET` | `/api/research/area/{id}` | Buscar área por ID |
| `PUT` | `/api/research/area/{id}` | Atualizar área de pesquisa |
| `DELETE` | `/api/research/area/{id}` | Remover área de pesquisa |

#### Exemplo de criação

```json
POST /api/research/area/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Exemplo Area de Pesquisa"
}
```

---

### Research Candidates (Candidatos de Pesquisa)

Todos os endpoints requerem autenticação ✅

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/research/{id}/match/run/` | Executar algoritmo de matching para a pesquisa manualmente (empresa)|
| `GET` | `/api/research/{id}/candidates/` | Listar candidatos da pesquisa (empresa) |
| `POST` | `/api/research/{id}/candidates/` | Indicar manualmente um pesquisador para a pesquisa (empresa) |
| `PATCH` | `/api/research/{id}/candidates/{candidate_id}/` | Alterar status de um candidato (empresa) |
| `POST` | `/api/research/{id}/interest/` | Demonstrar interesse em uma pesquisa (pesquisador) |
| `GET` | `/api/research/my-interests/` | Listar pesquisas de interesse do pesquisador autenticado |
| `GET` | `/api/research/my-suggestions/` | Listar sugestões manuais recebidas de empresas para o pesquisador autenticado |
| `GET` | `/api/research/my-recommendations/` | Listar pesquisas recomendadas por IA para o pesquisador autenticado |
| `POST` | `/api/research/my-suggestions/{candidate_id}/accept/` | Pesquisador aceita uma sugestão de empresa |
| `POST` | `/api/research/my-suggestions/{candidate_id}/reject/` | Pesquisador rejeita uma sugestão de empresa |
| `POST` | `/api/research/my-recommendations/{candidate_id}/accept/` | Pesquisador aceita uma recomendação da IA |
| `POST` | `/api/research/my-recommendations/{candidate_id}/reject/` | Pesquisador rejeita uma recomendação da IA |

#### Parâmetros de query para listagem de candidatos

| Parâmetro | Exemplo | Descrição |
|-----------|---------|-----------|
| `source` | `?source=ai` | Filtrar candidatos por origem (ex: `ai`) |
| `status` | `?status=under_review` | Filtrar candidatos por status |
| `ordering` | `?ordering=-score_match` | Ordenar por campo (prefixo `-` para decrescente) |

#### Executar matching

```json
POST /api/research/{id}/match/run/
Authorization: Bearer <token>
```

#### Listar candidatos com filtros

```
GET /api/research/{id}/candidates/
GET /api/research/{id}/candidates/?source=ai
GET /api/research/{id}/candidates/?status=under_review
GET /api/research/{id}/candidates/?ordering=-score_match
Authorization: Bearer <token>
```

#### Indicar manualmente um pesquisador na pesquisa

```
POST /api/research/{id}/candidates/
Authorization: Bearer <token>
Content-Type: application/json

{
  "researcher": 123
}
```

Esse fluxo permite que a empresa encontre um pesquisador em `/api/search/researchers/` e,
depois de escolher uma das suas pesquisas publicadas, o adicione como candidato manualmente.

#### Alterar status de candidato (empresa)

```json
PATCH /api/research/{id}/candidates/{candidate_id}/
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "under_review"
}
```

#### Demonstrar interesse em pesquisa (pesquisador)

```json
POST /api/research/{id}/interest/
Authorization: Bearer <token>
Content-Type: application/json

{
  "interest_message": "Tenho experiência nesse tema."
}
```

#### Listar interesses do pesquisador autenticado

```
GET /api/research/my-interests/
Authorization: Bearer <token>
```

#### Listar sugestões recebidas de empresas

```
GET /api/research/my-suggestions/
Authorization: Bearer <token>
```

#### Aceitar ou recusar sugestões de empresas

```
POST /api/research/my-suggestions/{candidate_id}/accept/
Authorization: Bearer <token>
```

```
POST /api/research/my-suggestions/{candidate_id}/reject/
Authorization: Bearer <token>
```

#### Atualização manual das recomendações do pesquisador autenticado

```
GET /api/research/my-recommendations/?refresh=true
Authorization: Bearer <token>
```

#### Aceitar ou recusar recomendações da IA

```
POST /api/research/my-recommendations/{candidate_id}/accept/
Authorization: Bearer <token>
```

```
POST /api/research/my-recommendations/{candidate_id}/reject/
Authorization: Bearer <token>
```

---

### Dashboard (Painel de Indicadores)

Todos os endpoints requerem autenticação ✅

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/dashboard/researcher/` | Painel com KPIs do pesquisador |
| `GET` | `/api/dashboard/company/` | Painel com KPIs da empresa |

#### Painel do pesquisador

```
GET /api/dashboard/researcher/
Authorization: Bearer <token>
```

#### Painel da empresa

```
GET /api/dashboard/company/
Authorization: Bearer <token>
```

Opcionalmente, a empresa pode filtrar um painel por pesquisa específica:

```
GET /api/dashboard/company/?research_id=123
Authorization: Bearer <token>
```

#### Estrutura do retorno

Os dois painéis usam as rotas acima, com o payload incluindo detalhes sobre o funil de candidatos:

- `summary.total_candidates`
- `summary.average_score`
- contadores separados por origem e status:
  - `summary.ai_suggested_candidates`
  - `summary.ai_interested_candidates`
  - `summary.ai_under_review_candidates`
  - `summary.ai_approved_candidates`
  - `summary.ai_rejected_candidates`
  - `summary.manual_suggested_candidates`
  - `summary.manual_interested_candidates`
  - `summary.manual_under_review_candidates`
  - `summary.manual_approved_candidates`
  - `summary.manual_rejected_candidates`
  - `summary.interest_suggested_candidates`
  - `summary.interest_interested_candidates`
  - `summary.interest_under_review_candidates`
  - `summary.interest_approved_candidates`
  - `summary.interest_rejected_candidates`
- `by_source`: total consolidado por origem
- `by_status`: total consolidado por status
- `by_source_status`: detalhamento de origem + status

No painel da empresa, o retorno também inclui:

- `researches`: lista de pesquisas da empresa com:
  - `total_candidates`
  - `average_score`
  - contadores por `source`
  - contadores por `status`

É possível acompanhar visualmente o fluxo completo:

1. IA sugeriu.
2. Empresa sugeriu manualmente.
3. Pesquisador aceitou ou rejeitou.
4. Empresa passou para análise, aprovou ou rejeitou.

---

### Universities (Universidades)

Todos os endpoints requerem autenticação ✅

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/universities/` | Listar todas as universidades |
| `POST` | `/api/universities/` | Criar universidade |
| `GET` | `/api/universities/{id}` | Buscar universidade por ID |
| `PUT` | `/api/universities/{id}` | Atualizar universidade |
| `DELETE` | `/api/universities/{id}` | Remover universidade |

#### Exemplo de criação

```json
POST /api/universities/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Exemplo Universidade"
}
```

---

### Experiences (Experiências)

Todos os endpoints requerem autenticação ✅

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/experiences/` | Listar todas as experiências |
| `POST` | `/api/experiences/` | Criar experiência |
| `GET` | `/api/experiences/{id}` | Buscar experiência por ID |
| `PUT` | `/api/experiences/{id}` | Atualizar experiência completa |
| `PATCH` | `/api/experiences/{id}` | Atualizar experiência parcialmente |
| `DELETE` | `/api/experiences/{id}` | Remover experiência |

#### Exemplo de criação

```json
POST /api/experiences/
Authorization: Bearer <token>
Content-Type: application/json

{
  "description": "Estagiario Backend",
  "start_date": "2024-01-01",
  "end_date": "2024-06-30",
  "resume": 1
}
```

---

### Educations (Formações)

Todos os endpoints requerem autenticação ✅

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/educations/` | Listar todas as formações |
| `POST` | `/api/educations/` | Criar formação |
| `GET` | `/api/educations/{id}` | Buscar formação por ID |
| `PUT` | `/api/educations/{id}` | Atualizar formação completa |
| `PATCH` | `/api/educations/{id}` | Atualizar formação parcialmente |
| `DELETE` | `/api/educations/{id}` | Remover formação |

#### Exemplo de criação

```json
POST /api/educations/
Authorization: Bearer <token>
Content-Type: application/json

{
  "course": "Sistemas de Informação",
  "institution": "Universidade XPTO",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "resume": 1
}
```

---

### Skills (Habilidades)

Todos os endpoints requerem autenticação ✅

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/skills/` | Listar todas as habilidades |
| `POST` | `/api/skills/` | Criar habilidade |
| `GET` | `/api/skills/{id}` | Buscar habilidade por ID |
| `PUT` | `/api/skills/{id}` | Atualizar habilidade |
| `DELETE` | `/api/skills/{id}` | Remover habilidade |

#### Exemplo de criação

```json
POST /api/skills/
Authorization: Bearer <token>
Content-Type: application/json

{
  "description": "JavaScript"
}
```

---

### Semantic Search (Busca Semântica)

Todos os endpoints requerem autenticação ✅

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/search/research/` | Buscar pesquisas por similaridade semântica (pesquisador) |
| `GET` | `/api/search/researchers/` | Buscar pesquisadores por similaridade semântica (empresa) |

#### Parâmetros de query

| Parâmetro | Exemplo | Descrição |
|--------|------|-----------|
| `q` | `?q=projeto para reduzir falhas industriais` | Texto de busca semântica |
| `limit` | `?limit=5` | Número máximo de resultados retornados |

#### Buscar pesquisas (pesquisador)

```json
GET /api/search/research/?q=projeto para reduzir falhas industriais usando analise de imagem&limit=5
Authorization: Bearer <token>
```
#### Buscar pesquisadores (empresa)

```json
GET /api/search/researchers/?q=especialista em interpretar dados visuais para controle de qualidade fabril&limit=5
Authorization: Bearer <token>
```

---

### Resumes (Currículos)

Todos os endpoints requerem autenticação ✅

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/resumes/` | Listar todos os currículos |
| `POST` | `/api/resumes/` | Criar currículo |
| `GET` | `/api/resumes/{id}` | Buscar currículo por ID |
| `PUT` | `/api/resumes/{id}` | Atualizar currículo |
| `DELETE` | `/api/resumes/{id}` | Remover currículo |

#### Exemplo de criação

```json
POST /api/resumes/
Authorization: Bearer <token>
Content-Type: application/json

{
  "skills": [6, 7]
}
```

---
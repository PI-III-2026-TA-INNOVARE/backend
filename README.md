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

---

## Documentação interativa

Acesse a documentação Swagger gerada automaticamente:

```
http://127.0.0.1:8000/api/docs/
```

---

## Rotas da API

Todas as rotas têm o prefixo `/api/`.

### Companies (Empresas)

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/companies/` | Listar todas as empresas |
| `POST` | `/api/companies/` | Criar empresa |
| `GET` | `/api/companies/{id}` | Buscar empresa por ID |
| `PUT` | `/api/companies/{id}` | Atualizar empresa completa |
| `PATCH` | `/api/companies/{id}` | Atualizar empresa parcialmente |
| `DELETE` | `/api/companies/{id}` | Remover empresa |

#### Exemplo de criação

```json
POST /api/companies/
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
Content-Type: application/json

{
  "name": "Pesquisador Exemplo",
  "availability": true,
  "status": true,
  "university": 1,
  "resume": 1
}
```

---

### Universities (Universidades)

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
Content-Type: application/json

{
  "name": "Exemplo Universidade"
}
```

---

### Experiences (Experiências)

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
Content-Type: application/json

{
  "description": "JavaScript"
}
```

---

### Resumes (Currículos)

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/resumes/` | Listar todos os currículos |
| `POST` | `/api/resumes/` | Criar currículo |
| `GET` | `/api/resumes/{id}` | Buscar currículo por ID |
| `PUT` | `/api/resumes/{id}` | Atualizar currículo |
| `DELETE` | `/api/resumes/{id}` | Remover currículo |

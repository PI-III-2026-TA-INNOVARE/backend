# P&D Connect — Backend Environment Image
#
# Esta imagem contém APENAS o ambiente pronto pra rodar o backend:
#   - Python 3.12
#   - Dependências do sistema (libpq, gcc, curl, git)
#   - Pacotes pip (Django, Celery, torch, sentence-transformers, etc.)
#
# Ela NÃO contém o código fonte. O código é montado como volume pelo
# docker-compose.yml em tempo de execução (`- .:/app`). Cada dev faz
# git clone do repo na própria máquina e o compose monta a pasta dentro
# do container.
#
# Vantagens:
#   - Imagem reutilizável (não precisa rebuildar a cada mudança de código)
#   - Código fonte fica só no Git/local, não vai pro Docker Hub
#   - Time só baixa a imagem 1x (deps pesadas como torch)
#
# Quando rebuildar e fazer push de novo:
#   - Quando mudar requirements.txt
#   - Quando mudar versão do Python ou pacotes do sistema

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependências de sistema:
#   - libpq-dev + gcc  → compilar psycopg2-binary
#   - curl             → healthchecks/diagnóstico
#   - git              → algumas libs de ML usam
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala as dependências Python — única coisa "imutável" na imagem.
# Se o requirements.txt mudar no repo, esta camada precisa ser rebuildada.
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# ATENÇÃO: nenhum "COPY . ." aqui — o código vem do volume montado pelo compose.

EXPOSE 8000

# CMD padrão (executa quando o compose não sobrescreve)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

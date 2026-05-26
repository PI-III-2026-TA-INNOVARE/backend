-- Habilita a extensão pgvector na database criada automaticamente pelo container.
-- Esse arquivo só roda quando o volume do Postgres é criado pela primeira vez
-- (ou seja, após um `docker compose down -v`).

CREATE EXTENSION IF NOT EXISTS vector;

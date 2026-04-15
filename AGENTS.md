# AGENTS.md — Knowledge Base Project

## Project Overview
- **Type**: Learning + resume-enhancing knowledge base system (RAG)
- **Stack**: Python 3.12, FastAPI, PostgreSQL + pgvector, SQLAlchemy 2.0 (async), Alembic
- **Repo**: https://github.com/zhanghao1903/knowledgebase

## Build & Run
```bash
# Local development
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Docker
docker compose up --build
```

## Project Structure
- `app/main.py` — FastAPI entry, lifespan, router registration
- `app/config.py` — pydantic-settings configuration
- `app/database.py` — Async SQLAlchemy engine, session, Base
- `app/models/` — SQLAlchemy ORM models (knowledge_base, document, chunk, task)
- `app/schemas/` — Pydantic request/response models
- `app/routers/` — API route handlers
- `app/services/` — Business logic layer
- `app/core/` — Custom exceptions
- `alembic/` — Database migrations
- `scripts/` — Utility scripts

## Database Tables
1. `knowledge_base` — KB metadata
2. `kb_document` — Document metadata + status
3. `kb_document_version` — Version history per document
4. `kb_chunk` — Text chunks with pgvector embedding
5. `task` — Async task tracking (pending/processing/success/failed)

## API Prefix
All business APIs under `/api/v1/`. Health check at `/health`.

## Code Style
- Async throughout (asyncpg, async SQLAlchemy sessions)
- Service layer pattern: routers → services → database
- UUID primary keys
- Pydantic v2 with `from_attributes = True`

## Development Phases
- Phase 1: ✅ Skeleton (models, APIs, Docker)
- Phase 2: TODO — Document parsing, chunking, embedding pipeline
- Phase 3: TODO — Query embedding, retrieval, LLM Q&A
- Phase 4: TODO — Polish, docs, demo preparation

## Key Design Decisions
- pgvector over standalone vector DB: simplicity, single Postgres handles both relational + vector
- Async task via DB polling (not Celery): simpler for prototype
- File stored on local disk: can swap to MinIO later
- Alembic for migrations: production-grade schema management

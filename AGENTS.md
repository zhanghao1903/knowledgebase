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

## Phase 2 Modules
- `app/services/parser.py` — PDF (pymupdf), TXT, DOCX (python-docx) text extraction
  - Returns `ParsedDocument` with list of `ParsedPage(page_number, text)`
- `app/services/chunker.py` — Sliding window chunking with overlap
  - Breaks at natural boundaries (paragraph, sentence, punctuation)
  - Returns `ChunkResult(content, chunk_index, page_number, char_start, char_end)`
- `app/services/embedding.py` — OpenAI-compatible embedding API client
  - Batched requests (64 texts/batch), configurable model/URL
- `app/services/ingest.py` — Full pipeline: parse → chunk → embed → store
  - Status flow: PENDING → PARSING → CHUNKING → EMBEDDING → READY (or FAILED)
- `app/worker.py` — Background asyncio task polling pending jobs every 3s

## Development Phases
- Phase 1: ✅ Skeleton (models, APIs, Docker)
- Phase 2: ✅ Document ingest pipeline (parse, chunk, embed, worker)
- Phase 3: TODO — Query embedding, retrieval, LLM Q&A
- Phase 4: TODO — Polish, docs, demo preparation

## Key Design Decisions
- pgvector over standalone vector DB: simplicity, single Postgres handles both relational + vector
- Async task via DB polling (not Celery): simpler for prototype
- Worker runs in-process as asyncio.create_task — no extra process needed
- File stored on local disk: can swap to MinIO later
- Alembic for migrations: production-grade schema management
- Chunking tries natural break points (newline, sentence-end punctuation) before hard split

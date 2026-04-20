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

## Phase 3 Modules
- `app/services/retrieval.py` — pgvector cosine distance search scoped to KB
  - Embeds query → cosine_distance search → returns RetrievedChunk with score
- `app/services/llm.py` — OpenAI-compatible chat completion client
- `app/services/qa.py` — Full RAG orchestrator: retrieve → build prompt → LLM → citations
  - System prompt enforces answer-from-context with citation numbers
- `app/schemas/qa.py` — QueryRequest, QueryResponse, Citation
- `app/routers/qa.py` — POST /api/v1/knowledge-bases/{kb_id}/query

## Phase 4: Testing
- `tests/conftest.py` — TestLogPlugin: auto-writes JSON report per run to `tests/logs/`
- `tests/unit/` — 44 cases: parser (13), chunker (16), qa_prompt (5), schemas (10)
- `tests/api/` — 25 cases: knowledge_base (10), document (7), task (5), qa (5)
  - Uses `_create_test_app()` with noop lifespan (no DB needed)
  - Model factories: `make_kb()`, `make_document()`, `make_task()`
- `pytest.ini` — markers: `unit`, `api`; asyncio_mode = auto
- `requirements-test.txt` — pytest + pytest-asyncio

## Phase 5: Engineering polish
- `app/core/error_handler.py` — Global exception handlers (404/422/500 uniform JSON)
- `app/main.py` — Enhanced health check (DB ping), startup config validation
- Document re-upload: PUT /documents/{id}/reupload → new version + re-ingest
- docker-compose.yml — All env vars (OpenRouter, Embedding) with defaults
- README: Mermaid architecture diagram, ER diagram, env var table, demo walkthrough

## Phase 6: Frontend
- Vue 3 + Vite SPA in `frontend/`
- 3 pages: HomeView (KB list), KBDetailView (docs + chat), TasksView
- API client: `frontend/src/api/client.js` (fetch wrapper with error handling)
- Components: ChatPanel, DocUpload (drag & drop), StatusBadge
- Nginx reverse proxy: `/api/*` → backend, SPA fallback for Vue Router
- Docker: multi-stage build (node:20-alpine → nginx:alpine)
- CORS middleware added to FastAPI `app/main.py`
- docker-compose.yml: `frontend` service on port 3500

## Development Phases
- Phase 1: ✅ Skeleton (models, APIs, Docker)
- Phase 2: ✅ Document ingest pipeline (parse, chunk, embed, worker)
- Phase 3: ✅ Retrieval & RAG Q&A (vector search, prompt, LLM, citations)
- Phase 4: ✅ Testing (75 tests: unit + API, with auto JSON logs)
- Phase 5: ✅ Engineering polish (error handling, version mgmt, architecture docs)
- Phase 6: ✅ Frontend (Vue 3 SPA: KB management, doc upload, Q&A chat, task monitor)

## Key Design Decisions
- pgvector over standalone vector DB: simplicity, single Postgres handles both relational + vector
- Async task via DB polling (not Celery): simpler for prototype
- Worker runs in-process as asyncio.create_task — no extra process needed
- File stored on local disk: can swap to MinIO later
- Alembic for migrations: production-grade schema management
- Chunking tries natural break points (newline, sentence-end punctuation) before hard split

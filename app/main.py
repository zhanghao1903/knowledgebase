import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.core.error_handler import register_error_handlers
from app.database import engine
from app.routers import knowledge_base, document, task, qa
from app.worker import worker_loop

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
)


def _check_config() -> None:
    """Warn about placeholder configuration values on startup."""
    if settings.OPENROUTER_API_KEY in ("sk-placeholder", ""):
        logger.warning("⚠️  OPENROUTER_API_KEY is not configured — LLM Q&A will fail")
    if settings.effective_embedding_api_key in ("sk-placeholder", ""):
        logger.warning("⚠️  Embedding API key is not configured — document ingest will fail")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Check configuration
    _check_config()

    # Enable pgvector extension on startup
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    # Start background worker
    worker_task = asyncio.create_task(worker_loop())
    logger.info("🚀 Knowledge Base API started (version %s)", settings.VERSION)

    yield

    # Graceful shutdown
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    await engine.dispose()
    logger.info("Knowledge Base API stopped")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="一个小而完整的知识库系统，支持文档上传、解析、切块、向量化、检索与问答。",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

app.include_router(knowledge_base.router, prefix="/api/v1")
app.include_router(document.router, prefix="/api/v1")
app.include_router(task.router, prefix="/api/v1")
app.include_router(qa.router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查，包含数据库连通性检测"""
    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        logger.warning("Health check: database unreachable")

    status = "ok" if db_ok else "degraded"
    return {
        "status": status,
        "version": settings.VERSION,
        "database": "connected" if db_ok else "unreachable",
    }

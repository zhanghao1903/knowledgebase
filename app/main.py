from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.routers import knowledge_base, document, task


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enable pgvector extension on startup
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="一个小而完整的知识库系统，支持文档上传、解析、切块、向量化、检索与问答。",
    lifespan=lifespan,
)

app.include_router(knowledge_base.router, prefix="/api/v1")
app.include_router(document.router, prefix="/api/v1")
app.include_router(task.router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": settings.VERSION}

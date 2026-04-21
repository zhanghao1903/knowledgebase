"""API test fixtures — provides a TestClient with mocked DB dependency.

The lifespan is replaced with a no-op so tests don't need PostgreSQL.
"""
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import settings
from app.database import get_db
from app.models.document import (
    Document,
    DocumentStatus,
    DocumentVersion,
    FileType,
    SourceType,
)
from app.models.knowledge_base import KnowledgeBase
from app.models.task import Task, TaskStatus, TaskType


def _create_test_app() -> FastAPI:
    """Build a FastAPI app identical to production but with a no-op lifespan."""
    from app.core.error_handler import register_error_handlers
    from app.routers import knowledge_base, document, task, qa

    @asynccontextmanager
    async def _noop_lifespan(app: FastAPI):
        yield

    test_app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=_noop_lifespan,
    )
    register_error_handlers(test_app)
    test_app.include_router(knowledge_base.router, prefix="/api/v1")
    test_app.include_router(document.router, prefix="/api/v1")
    test_app.include_router(task.router, prefix="/api/v1")
    test_app.include_router(qa.router, prefix="/api/v1")
    return test_app


@pytest.fixture
def mock_db():
    """An AsyncMock that stands in for the DB session."""
    return AsyncMock()


@pytest.fixture
def client(mock_db):
    """FastAPI TestClient with the DB dependency overridden and no real lifespan."""
    test_app = _create_test_app()
    test_app.dependency_overrides[get_db] = lambda: mock_db
    with TestClient(test_app, raise_server_exceptions=False) as c:
        yield c
    test_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Factory helpers — use normal constructors with all fields explicit
# so SQLAlchemy instrumentation works without a real DB.
# ---------------------------------------------------------------------------

def make_kb(
    name: str = "测试知识库",
    description: str | None = "测试用",
    document_count: int = 0,
) -> KnowledgeBase:
    now = datetime.now(timezone.utc)
    return KnowledgeBase(
        id=uuid.uuid4(),
        name=name,
        description=description,
        document_count=document_count,
        created_at=now,
        updated_at=now,
    )


def make_document(
    kb_id: uuid.UUID | None = None,
    filename: str = "test.pdf",
    status: DocumentStatus = DocumentStatus.READY,
    source_type: SourceType = SourceType.FILE,
    source_url: str | None = None,
    file_type: FileType = FileType.PDF,
) -> Document:
    now = datetime.now(timezone.utc)
    return Document(
        id=uuid.uuid4(),
        knowledge_base_id=kb_id or uuid.uuid4(),
        filename=filename,
        file_type=file_type,
        file_size=1024,
        file_path="/tmp/test.pdf",
        source_type=source_type,
        source_url=source_url,
        content_hash=None,
        status=status,
        current_version=1,
        chunk_count=5,
        error_message=None,
        created_at=now,
        updated_at=now,
    )


def make_task(
    document_id: uuid.UUID | None = None,
    status: TaskStatus = TaskStatus.SUCCESS,
) -> Task:
    now = datetime.now(timezone.utc)
    return Task(
        id=uuid.uuid4(),
        document_id=document_id or uuid.uuid4(),
        task_type=TaskType.DOCUMENT_INGEST,
        status=status,
        error_message=None,
        created_at=now,
        updated_at=now,
        completed_at=now,
    )

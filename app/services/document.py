import os
import re
import uuid
from pathlib import Path
from urllib.parse import urlparse

from fastapi import UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    NotFoundError,
    UnsupportedFileTypeError,
    UnsupportedSourceOperationError,
)
from app.models.document import (
    Document,
    DocumentStatus,
    DocumentVersion,
    FileType,
    SourceType,
)
from app.models.knowledge_base import KnowledgeBase
from app.models.task import Task, TaskType, TaskStatus
from app.services.fetcher import FetchedResource, fetch_url

# Only user-uploaded file types; HTML is produced internally from URL fetches.
ALLOWED_EXTENSIONS = {"pdf", "txt", "docx"}


def _get_file_type(filename: str) -> FileType:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(ext or filename)
    return FileType(ext)


def _title_to_filename(title: str, fallback_url: str) -> str:
    """Turn a page <title> into something safe for display + storage."""
    title = (title or "").strip()
    if not title:
        parsed = urlparse(fallback_url)
        title = f"{parsed.hostname or 'page'}{parsed.path or ''}".rstrip("/")
    # Collapse whitespace and trim to a reasonable length for the filename col.
    title = re.sub(r"\s+", " ", title)
    return title[:255] or "url-document"


def _slugify(value: str) -> str:
    """Produce a short, filesystem-safe slug for the on-disk snapshot filename."""
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return (slug or "snapshot")[:80]


async def upload_document(
    db: AsyncSession, kb_id: uuid.UUID, file: UploadFile
) -> tuple[Document, Task]:
    # Verify knowledge base exists
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        raise NotFoundError("KnowledgeBase", kb_id)

    file_type = _get_file_type(file.filename or "unknown")

    # Save file to storage
    doc_id = uuid.uuid4()
    storage_dir = Path(settings.STORAGE_DIR) / str(kb_id) / str(doc_id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    file_path = storage_dir / f"v1_{file.filename}"

    content = await file.read()
    file_size = len(content)
    with open(file_path, "wb") as f:
        f.write(content)

    # Create document record
    doc = Document(
        id=doc_id,
        knowledge_base_id=kb_id,
        filename=file.filename,
        file_type=file_type,
        file_size=file_size,
        file_path=str(file_path),
        source_type=SourceType.FILE,
        status=DocumentStatus.PENDING,
        current_version=1,
    )
    db.add(doc)

    # Create version record
    version = DocumentVersion(
        document_id=doc_id,
        version_number=1,
        file_path=str(file_path),
        file_size=file_size,
    )
    db.add(version)

    # Flush document + version first so the FK target exists
    kb.document_count = kb.document_count + 1
    await db.flush()

    # Create ingest task (depends on document via FK)
    task = Task(
        document_id=doc.id,
        task_type=TaskType.DOCUMENT_INGEST,
        status=TaskStatus.PENDING,
    )
    db.add(task)
    await db.flush()

    await db.refresh(doc)
    await db.refresh(task)
    return doc, task


async def reupload_document(
    db: AsyncSession, doc_id: uuid.UUID, file: UploadFile
) -> tuple[Document, Task]:
    """Re-upload a document, creating a new version and re-triggering ingest."""
    doc = await get_document(db, doc_id)

    if doc.source_type == SourceType.URL:
        raise UnsupportedSourceOperationError(
            "This document was ingested from a URL. Use POST "
            "/documents/{id}/recrawl to refresh it."
        )

    new_file_type = _get_file_type(file.filename or "unknown")

    # Increment version
    new_version = doc.current_version + 1

    # Save file
    storage_dir = Path(settings.STORAGE_DIR) / str(doc.knowledge_base_id) / str(doc.id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    file_path = storage_dir / f"v{new_version}_{file.filename}"

    content = await file.read()
    file_size = len(content)
    with open(file_path, "wb") as f:
        f.write(content)

    # Update document record
    doc.filename = file.filename
    doc.file_type = new_file_type
    doc.file_size = file_size
    doc.file_path = str(file_path)
    doc.current_version = new_version
    doc.status = DocumentStatus.PENDING
    doc.error_message = None

    # Create version record
    version = DocumentVersion(
        document_id=doc.id,
        version_number=new_version,
        file_path=str(file_path),
        file_size=file_size,
    )
    db.add(version)

    # Flush document update + version first
    await db.flush()

    # Create new ingest task (depends on document via FK)
    task = Task(
        document_id=doc.id,
        task_type=TaskType.DOCUMENT_INGEST,
        status=TaskStatus.PENDING,
    )
    db.add(task)
    await db.flush()

    await db.refresh(doc)
    await db.refresh(task)
    return doc, task


async def get_document(db: AsyncSession, doc_id: uuid.UUID) -> Document:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise NotFoundError("Document", doc_id)
    return doc


async def list_documents(
    db: AsyncSession, kb_id: uuid.UUID, offset: int = 0, limit: int = 20
) -> tuple[list[Document], int]:
    count_result = await db.execute(
        select(func.count(Document.id)).where(Document.knowledge_base_id == kb_id)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Document)
        .where(Document.knowledge_base_id == kb_id)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list(result.scalars().all())
    return items, total


async def get_document_versions(
    db: AsyncSession, doc_id: uuid.UUID
) -> list[DocumentVersion]:
    result = await db.execute(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == doc_id)
        .order_by(DocumentVersion.version_number.desc())
    )
    return list(result.scalars().all())


def _save_url_snapshot(
    kb_id: uuid.UUID, doc_id: uuid.UUID, version: int, fetched: FetchedResource
) -> Path:
    """Persist the raw HTML bytes to ./storage, matching file-upload layout."""
    storage_dir = Path(settings.STORAGE_DIR) / str(kb_id) / str(doc_id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    slug = _slugify(urlparse(fetched.url).hostname or "snapshot")
    path = storage_dir / f"v{version}_{slug}.html"
    path.write_bytes(fetched.content)
    return path


async def upload_url_document(
    db: AsyncSession, kb_id: uuid.UUID, url: str
) -> tuple[Document, Task]:
    """Fetch a URL, persist the HTML snapshot, and create Document + Task.

    The fetcher runs BEFORE any DB writes so that a fetch failure leaves no
    Document behind. Once fetching succeeds, the document goes through the
    normal ingest pipeline (parse_html → chunk → embed) via the worker.
    """
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        raise NotFoundError("KnowledgeBase", kb_id)

    fetched = await fetch_url(url)

    doc_id = uuid.uuid4()
    file_path = _save_url_snapshot(kb_id, doc_id, version=1, fetched=fetched)
    filename = _title_to_filename(fetched.title, fetched.url)

    doc = Document(
        id=doc_id,
        knowledge_base_id=kb_id,
        filename=filename,
        file_type=FileType.HTML,
        file_size=len(fetched.content),
        file_path=str(file_path),
        source_type=SourceType.URL,
        source_url=fetched.url,
        content_hash=fetched.content_hash,
        status=DocumentStatus.PENDING,
        current_version=1,
    )
    db.add(doc)

    version = DocumentVersion(
        document_id=doc_id,
        version_number=1,
        file_path=str(file_path),
        file_size=len(fetched.content),
        source_url=fetched.url,
        content_hash=fetched.content_hash,
    )
    db.add(version)

    kb.document_count = kb.document_count + 1
    await db.flush()

    task = Task(
        document_id=doc.id,
        task_type=TaskType.DOCUMENT_INGEST,
        status=TaskStatus.PENDING,
    )
    db.add(task)
    await db.flush()

    await db.refresh(doc)
    await db.refresh(task)
    return doc, task


async def recrawl_url_document(
    db: AsyncSession, doc_id: uuid.UUID
) -> tuple[Document, Task | None, bool]:
    """Re-fetch a URL document; create a new version only if content changed.

    Returns (document, task_or_None, changed). When content is unchanged we
    skip the new version/task and simply report back to the caller.
    """
    doc = await get_document(db, doc_id)
    if doc.source_type != SourceType.URL or not doc.source_url:
        raise UnsupportedSourceOperationError(
            "Recrawl is only supported for URL-sourced documents. "
            "For uploaded files, use PUT /documents/{id}/reupload."
        )

    fetched = await fetch_url(doc.source_url)

    if fetched.content_hash == doc.content_hash:
        await db.refresh(doc)
        return doc, None, False

    new_version = doc.current_version + 1
    file_path = _save_url_snapshot(
        doc.knowledge_base_id, doc.id, version=new_version, fetched=fetched
    )

    doc.filename = _title_to_filename(fetched.title, fetched.url)
    doc.file_size = len(fetched.content)
    doc.file_path = str(file_path)
    doc.source_url = fetched.url  # in case of redirects / normalization
    doc.content_hash = fetched.content_hash
    doc.current_version = new_version
    doc.status = DocumentStatus.PENDING
    doc.error_message = None

    version = DocumentVersion(
        document_id=doc.id,
        version_number=new_version,
        file_path=str(file_path),
        file_size=len(fetched.content),
        source_url=fetched.url,
        content_hash=fetched.content_hash,
    )
    db.add(version)
    await db.flush()

    task = Task(
        document_id=doc.id,
        task_type=TaskType.DOCUMENT_INGEST,
        status=TaskStatus.PENDING,
    )
    db.add(task)
    await db.flush()

    await db.refresh(doc)
    await db.refresh(task)
    return doc, task, True


async def delete_document(db: AsyncSession, doc_id: uuid.UUID) -> None:
    doc = await get_document(db, doc_id)

    # Update knowledge base document count
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == doc.knowledge_base_id)
    )
    kb = result.scalar_one_or_none()
    if kb and kb.document_count > 0:
        kb.document_count = kb.document_count - 1

    # Remove file from storage
    file_path = Path(doc.file_path)
    if file_path.exists():
        storage_dir = file_path.parent
        for f in storage_dir.iterdir():
            f.unlink()
        storage_dir.rmdir()

    await db.delete(doc)
    await db.flush()

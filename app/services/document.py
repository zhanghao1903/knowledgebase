import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import NotFoundError, UnsupportedFileTypeError
from app.models.document import Document, DocumentVersion, DocumentStatus, FileType
from app.models.knowledge_base import KnowledgeBase
from app.models.task import Task, TaskType, TaskStatus

ALLOWED_EXTENSIONS = {"pdf", "txt", "docx"}


def _get_file_type(filename: str) -> FileType:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(ext or filename)
    return FileType(ext)


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

    # Create ingest task
    task = Task(
        document_id=doc_id,
        task_type=TaskType.DOCUMENT_INGEST,
        status=TaskStatus.PENDING,
    )
    db.add(task)

    # Update knowledge base document count
    kb.document_count = kb.document_count + 1

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

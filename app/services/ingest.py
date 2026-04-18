"""Document ingestion pipeline: parse → chunk → embed → store.

Orchestrates the full flow from a raw file to searchable vector chunks.
Each step updates document/task status for observability.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.document import Document, DocumentStatus
from app.models.task import Task, TaskStatus
from app.services.chunker import chunk_document
from app.services.embedding import get_embeddings
from app.services.parser import parse_file

logger = logging.getLogger(__name__)


async def run_ingest(task_id: uuid.UUID, db: AsyncSession) -> None:
    """Execute the full ingest pipeline for a given task."""
    # Load task and document
    task = (await db.execute(select(Task).where(Task.id == task_id))).scalar_one()
    doc = (await db.execute(select(Document).where(Document.id == task.document_id))).scalar_one()

    task.status = TaskStatus.PROCESSING
    await db.flush()

    try:
        # --- Step 1: Parse ---
        doc.status = DocumentStatus.PARSING
        await db.flush()
        logger.info("[%s] Parsing %s (%s)", doc.id, doc.filename, doc.file_type.value)

        parsed = parse_file(doc.file_path, doc.file_type.value)
        if not parsed.full_text.strip():
            raise ValueError("Document is empty after parsing")

        # --- Step 2: Chunk ---
        doc.status = DocumentStatus.CHUNKING
        await db.flush()
        logger.info("[%s] Chunking text (%d chars)", doc.id, len(parsed.full_text))

        chunks = chunk_document(parsed)
        if not chunks:
            raise ValueError("No chunks produced from document")

        # --- Step 3: Embed ---
        doc.status = DocumentStatus.EMBEDDING
        await db.flush()
        logger.info("[%s] Embedding %d chunks", doc.id, len(chunks))

        texts = [c.content for c in chunks]
        embeddings = await get_embeddings(texts)

        # --- Step 4: Store chunks ---
        logger.info("[%s] Storing %d chunks to database", doc.id, len(chunks))

        # Remove old chunks for this document (in case of re-ingest)
        old_chunks = (await db.execute(
            select(Chunk).where(Chunk.document_id == doc.id)
        )).scalars().all()
        for old in old_chunks:
            await db.delete(old)
        await db.flush()

        for chunk_result, embedding in zip(chunks, embeddings):
            db_chunk = Chunk(
                document_id=doc.id,
                version_number=doc.current_version,
                content=chunk_result.content,
                chunk_index=chunk_result.chunk_index,
                page_number=chunk_result.page_number,
                metadata_={
                    "char_start": chunk_result.char_start,
                    "char_end": chunk_result.char_end,
                    "filename": doc.filename,
                },
                embedding=embedding,
            )
            db.add(db_chunk)

        # --- Done ---
        doc.status = DocumentStatus.READY
        doc.chunk_count = len(chunks)
        doc.error_message = None
        task.status = TaskStatus.SUCCESS
        task.completed_at = datetime.now(timezone.utc)
        await db.flush()

        logger.info("[%s] Ingest complete: %d chunks stored", doc.id, len(chunks))

    except Exception as e:
        logger.exception("[%s] Ingest failed: %s", doc.id, e)
        doc.status = DocumentStatus.FAILED
        doc.error_message = str(e)[:2000]
        task.status = TaskStatus.FAILED
        task.error_message = str(e)[:2000]
        task.completed_at = datetime.now(timezone.utc)
        await db.flush()

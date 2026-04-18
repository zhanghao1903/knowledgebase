"""Vector retrieval service — search pgvector for similar chunks.

Embeds the user query, then performs cosine distance search
scoped to a specific knowledge base's ready documents.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.chunk import Chunk
from app.models.document import Document, DocumentStatus
from app.services.embedding import get_embeddings

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    content: str
    chunk_index: int
    page_number: int | None
    filename: str
    score: float  # cosine similarity (1 - distance)


async def search(
    db: AsyncSession,
    kb_id: uuid.UUID,
    query: str,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    """Retrieve the most relevant chunks for a query within a knowledge base."""
    k = top_k or settings.RETRIEVAL_TOP_K

    # Embed the query
    embeddings = await get_embeddings([query])
    query_vector = embeddings[0]

    # Find document IDs that belong to this KB and are ready
    doc_subquery = (
        select(Document.id)
        .where(Document.knowledge_base_id == kb_id)
        .where(Document.status == DocumentStatus.READY)
    ).subquery()

    # pgvector cosine distance: embedding <=> query_vector
    distance = Chunk.embedding.cosine_distance(query_vector)

    stmt = (
        select(
            Chunk,
            Document.filename,
            distance.label("distance"),
        )
        .join(Document, Chunk.document_id == Document.id)
        .where(Chunk.document_id.in_(select(doc_subquery.c.id)))
        .where(Chunk.embedding.isnot(None))
        .order_by(distance)
        .limit(k)
    )

    result = await db.execute(stmt)
    rows = result.all()

    retrieved = []
    for chunk, filename, dist in rows:
        retrieved.append(RetrievedChunk(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            content=chunk.content,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            filename=filename,
            score=round(1.0 - float(dist), 4),  # cosine similarity
        ))

    logger.info("Retrieved %d chunks for query (top_k=%d)", len(retrieved), k)
    return retrieved

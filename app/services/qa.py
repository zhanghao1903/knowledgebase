"""Question-answering service — orchestrates the full RAG flow.

retrieve relevant chunks → build prompt with citations → call LLM → return
structured answer with source references.
"""
from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm import chat_completion
from app.services.retrieval import RetrievedChunk, search

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个知识库问答助手。请严格根据下方提供的【参考资料】来回答用户的问题。

规则：
1. 只使用参考资料中的信息来回答，不要编造内容。
2. 在回答中引用来源编号，例如 [1]、[2]。
3. 如果参考资料不足以回答问题，请如实说明"根据已有资料无法回答该问题"。
4. 回答应简洁、准确、有条理。"""


def _build_user_message(question: str, chunks: list[RetrievedChunk]) -> str:
    """Build the user message containing retrieved context and the question."""
    if not chunks:
        return f"（未找到相关参考资料）\n\n用户问题：{question}"

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.filename
        page_info = f"页码: {chunk.page_number}" if chunk.page_number else "页码: -"
        context_parts.append(
            f"[{i}] (来源: {source}, {page_info})\n{chunk.content}"
        )

    context = "\n\n".join(context_parts)
    return f"参考资料：\n---\n{context}\n---\n\n用户问题：{question}"


async def ask(
    db: AsyncSession,
    kb_id: uuid.UUID,
    question: str,
    top_k: int | None = None,
) -> dict:
    """Execute the full RAG pipeline: retrieve → prompt → LLM → answer + citations."""
    # Step 1: Retrieve relevant chunks
    chunks = await search(db, kb_id, question, top_k=top_k)
    logger.info("Retrieved %d chunks for Q&A", len(chunks))

    # Step 2: Build prompt and call LLM
    user_message = _build_user_message(question, chunks)
    answer = await chat_completion(SYSTEM_PROMPT, user_message)

    # Step 3: Build citations from retrieved chunks
    citations = [
        {
            "index": i,
            "chunk_id": str(chunk.chunk_id),
            "document_id": str(chunk.document_id),
            "content": chunk.content,
            "page_number": chunk.page_number,
            "filename": chunk.filename,
            "score": chunk.score,
        }
        for i, chunk in enumerate(chunks, 1)
    ]

    return {
        "question": question,
        "answer": answer,
        "citations": citations,
    }

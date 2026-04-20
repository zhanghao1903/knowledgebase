"""Embedding client — wraps an OpenAI-compatible embedding API.

Provides batch embedding with automatic chunking to respect API limits.
Note: OpenRouter does not serve embeddings, so this typically points to
a separate provider (OpenAI, local model, etc.) configured via
EMBEDDING_API_URL and EMBEDDING_API_KEY.
"""
from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

BATCH_SIZE = 64  # max texts per API call


async def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings for a list of texts via OpenAI-compatible API.

    Automatically splits into batches if texts exceed BATCH_SIZE.
    Returns a list of embedding vectors in the same order as input.
    """
    if not texts:
        return []

    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        batch_embeddings = await _call_embedding_api(batch)
        all_embeddings.extend(batch_embeddings)

    return all_embeddings


async def _call_embedding_api(texts: list[str]) -> list[list[float]]:
    """Call the embedding API for a single batch."""
    payload = {
        "input": texts,
        "model": settings.EMBEDDING_MODEL,
        "dimensions": 1536,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.effective_embedding_api_key}",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        logger.info(
            "Calling embedding API: %s, model=%s, batch_size=%d",
            settings.EMBEDDING_API_URL,
            settings.EMBEDDING_MODEL,
            len(texts),
        )
        resp = await client.post(
            settings.EMBEDDING_API_URL,
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()

    data = resp.json()
    # OpenAI format: {"data": [{"embedding": [...], "index": 0}, ...]}
    sorted_items = sorted(data["data"], key=lambda x: x["index"])
    return [item["embedding"] for item in sorted_items]

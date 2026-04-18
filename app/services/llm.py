"""LLM client — wraps an OpenAI-compatible chat completion API.

Provides a simple interface for generating answers from a prompt.
Designed to be swappable: change the URL/model in config.
"""
from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def chat_completion(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> str:
    """Call the LLM API and return the assistant's response text."""
    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        logger.info(
            "Calling LLM API: %s, model=%s",
            settings.LLM_API_URL,
            settings.LLM_MODEL,
        )
        resp = await client.post(
            settings.LLM_API_URL,
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()

    data = resp.json()
    answer = data["choices"][0]["message"]["content"]
    logger.info("LLM response received (%d chars)", len(answer))
    return answer

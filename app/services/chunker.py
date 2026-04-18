"""Text chunking with sliding window strategy.

Splits parsed document pages into overlapping chunks while preserving
the mapping between each chunk and its source page number.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from app.config import settings
from app.services.parser import ParsedDocument

logger = logging.getLogger(__name__)


@dataclass
class ChunkResult:
    content: str
    chunk_index: int
    page_number: int | None
    char_start: int
    char_end: int


def chunk_document(
    parsed: ParsedDocument,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[ChunkResult]:
    """Split a parsed document into overlapping text chunks.

    For multi-page documents (PDF), each page is chunked independently
    so page_number mapping stays accurate. For single-page documents
    (TXT/DOCX), the full text is chunked as one stream.
    """
    size = chunk_size or settings.CHUNK_SIZE
    overlap = chunk_overlap or settings.CHUNK_OVERLAP

    if size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap >= size:
        raise ValueError("chunk_overlap must be less than chunk_size")

    chunks: list[ChunkResult] = []
    global_index = 0

    for page in parsed.pages:
        text = page.text.strip()
        if not text:
            continue

        page_chunks = _split_text(text, size, overlap)
        for content, char_start, char_end in page_chunks:
            chunks.append(ChunkResult(
                content=content,
                chunk_index=global_index,
                page_number=page.page_number,
                char_start=char_start,
                char_end=char_end,
            ))
            global_index += 1

    logger.info("Chunked into %d pieces (size=%d, overlap=%d)", len(chunks), size, overlap)
    return chunks


def _split_text(
    text: str, chunk_size: int, overlap: int
) -> list[tuple[str, int, int]]:
    """Split a single text string into (content, start, end) tuples."""
    results = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        # Try to break at sentence/paragraph boundary when not at the end
        if end < text_len:
            # Look backward for a good break point
            search_start = max(start + chunk_size // 2, start)
            best_break = -1
            for sep in ["\n\n", "\n", "。", ".", "！", "!", "？", "?", "；", ";", " "]:
                pos = text.rfind(sep, search_start, end)
                if pos != -1:
                    best_break = pos + len(sep)
                    break
            if best_break > start:
                end = best_break

        chunk_text = text[start:end].strip()
        if chunk_text:
            results.append((chunk_text, start, end))

        # Advance with overlap
        if end >= text_len:
            break
        start = end - overlap

    return results

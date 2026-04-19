"""Unit tests for RAG prompt building logic."""
import uuid

import pytest

from app.services.qa import _build_user_message
from app.services.retrieval import RetrievedChunk

pytestmark = pytest.mark.unit


def _make_chunk(content: str, filename: str = "doc.pdf",
                page_number: int | None = 1, score: float = 0.9) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        content=content,
        chunk_index=0,
        page_number=page_number,
        filename=filename,
        score=score,
    )


class TestBuildUserMessage:
    def test_with_chunks(self):
        chunks = [
            _make_chunk("First chunk content", "报告.pdf", page_number=3),
            _make_chunk("Second chunk content", "说明.docx", page_number=1),
        ]
        msg = _build_user_message("什么是RAG？", chunks)

        assert "参考资料" in msg
        assert "[1]" in msg
        assert "[2]" in msg
        assert "报告.pdf" in msg
        assert "说明.docx" in msg
        assert "页码: 3" in msg
        assert "页码: 1" in msg
        assert "First chunk content" in msg
        assert "Second chunk content" in msg
        assert "用户问题：什么是RAG？" in msg

    def test_empty_chunks(self):
        msg = _build_user_message("测试问题", [])
        assert "未找到相关参考资料" in msg
        assert "用户问题：测试问题" in msg

    def test_page_number_none(self):
        chunks = [_make_chunk("content", page_number=None)]
        msg = _build_user_message("question", chunks)
        assert "页码: -" in msg

    def test_question_preserved(self):
        chunks = [_make_chunk("ctx")]
        question = "这个系统支持什么文件格式？"
        msg = _build_user_message(question, chunks)
        assert question in msg

    def test_citation_ordering(self):
        chunks = [
            _make_chunk(f"chunk_{i}", f"file_{i}.pdf")
            for i in range(5)
        ]
        msg = _build_user_message("q", chunks)
        for i in range(1, 6):
            assert f"[{i}]" in msg
            assert f"file_{i - 1}.pdf" in msg

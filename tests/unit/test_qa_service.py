"""Unit tests for QA orchestration service (app/services/qa.py).

Mocks both retrieval.search and llm.chat_completion — tests the
orchestration logic, prompt building, and citation formatting.
"""
import uuid

import pytest
from unittest.mock import AsyncMock, patch

from app.services.retrieval import RetrievedChunk

pytestmark = pytest.mark.unit


def _make_chunks(n=3):
    return [
        RetrievedChunk(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            content=f"Chunk content #{i}",
            chunk_index=i,
            page_number=i + 1,
            filename=f"doc_{i}.pdf",
            score=round(0.95 - i * 0.05, 2),
        )
        for i in range(n)
    ]


class TestAsk:
    @pytest.mark.asyncio
    async def test_full_flow(self):
        """ask() should call search, then chat_completion, then return structured result."""
        chunks = _make_chunks(2)
        with (
            patch("app.services.qa.search", new_callable=AsyncMock, return_value=chunks),
            patch("app.services.qa.chat_completion", new_callable=AsyncMock, return_value="LLM回答"),
        ):
            from app.services.qa import ask
            result = await ask(AsyncMock(), uuid.uuid4(), "测试问题")

        assert result["question"] == "测试问题"
        assert result["answer"] == "LLM回答"
        assert len(result["citations"]) == 2

    @pytest.mark.asyncio
    async def test_return_structure(self):
        """Return dict must have exactly question, answer, citations keys."""
        with (
            patch("app.services.qa.search", new_callable=AsyncMock, return_value=_make_chunks(1)),
            patch("app.services.qa.chat_completion", new_callable=AsyncMock, return_value="ans"),
        ):
            from app.services.qa import ask
            result = await ask(AsyncMock(), uuid.uuid4(), "q")

        assert set(result.keys()) == {"question", "answer", "citations"}

    @pytest.mark.asyncio
    async def test_citations_format(self):
        """Each citation should contain required fields."""
        chunks = _make_chunks(1)
        with (
            patch("app.services.qa.search", new_callable=AsyncMock, return_value=chunks),
            patch("app.services.qa.chat_completion", new_callable=AsyncMock, return_value="a"),
        ):
            from app.services.qa import ask
            result = await ask(AsyncMock(), uuid.uuid4(), "q")

        c = result["citations"][0]
        required_keys = {"index", "chunk_id", "document_id", "content", "page_number", "filename", "score"}
        assert required_keys.issubset(set(c.keys()))
        assert c["index"] == 1
        assert c["filename"] == "doc_0.pdf"
        assert c["page_number"] == 1
        assert isinstance(c["score"], float)

    @pytest.mark.asyncio
    async def test_empty_retrieval(self):
        """No chunks found — should still call LLM and return empty citations."""
        with (
            patch("app.services.qa.search", new_callable=AsyncMock, return_value=[]),
            patch("app.services.qa.chat_completion", new_callable=AsyncMock, return_value="无资料") as mock_llm,
        ):
            from app.services.qa import ask
            result = await ask(AsyncMock(), uuid.uuid4(), "没有答案的问题")

        assert result["answer"] == "无资料"
        assert result["citations"] == []
        # LLM was still called
        mock_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_top_k_forwarded(self):
        """top_k parameter should be passed through to search."""
        with (
            patch("app.services.qa.search", new_callable=AsyncMock, return_value=[]) as mock_search,
            patch("app.services.qa.chat_completion", new_callable=AsyncMock, return_value="a"),
        ):
            from app.services.qa import ask
            kb_id = uuid.uuid4()
            await ask(AsyncMock(), kb_id, "q", top_k=10)

        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args
        assert call_kwargs.kwargs.get("top_k") == 10 or call_kwargs[0][-1] == 10

    @pytest.mark.asyncio
    async def test_prompt_contains_chunks(self):
        """The user message passed to LLM should contain chunk contents."""
        chunks = _make_chunks(2)
        with (
            patch("app.services.qa.search", new_callable=AsyncMock, return_value=chunks),
            patch("app.services.qa.chat_completion", new_callable=AsyncMock, return_value="a") as mock_llm,
        ):
            from app.services.qa import ask
            await ask(AsyncMock(), uuid.uuid4(), "用户问题")

        user_msg = mock_llm.call_args[0][1]  # second positional arg
        assert "Chunk content #0" in user_msg
        assert "Chunk content #1" in user_msg
        assert "用户问题" in user_msg

    @pytest.mark.asyncio
    async def test_system_prompt_not_empty(self):
        """System prompt passed to LLM should be the knowledge base assistant prompt."""
        with (
            patch("app.services.qa.search", new_callable=AsyncMock, return_value=[]),
            patch("app.services.qa.chat_completion", new_callable=AsyncMock, return_value="a") as mock_llm,
        ):
            from app.services.qa import ask
            await ask(AsyncMock(), uuid.uuid4(), "q")

        system_prompt = mock_llm.call_args[0][0]
        assert len(system_prompt) > 50
        assert "知识库" in system_prompt or "参考资料" in system_prompt

    @pytest.mark.asyncio
    async def test_citation_ids_are_strings(self):
        """chunk_id and document_id in citations should be serialized as strings."""
        chunks = _make_chunks(1)
        with (
            patch("app.services.qa.search", new_callable=AsyncMock, return_value=chunks),
            patch("app.services.qa.chat_completion", new_callable=AsyncMock, return_value="a"),
        ):
            from app.services.qa import ask
            result = await ask(AsyncMock(), uuid.uuid4(), "q")

        c = result["citations"][0]
        assert isinstance(c["chunk_id"], str)
        assert isinstance(c["document_id"], str)

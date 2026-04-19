"""API tests for Q&A (RAG) endpoint."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

pytestmark = pytest.mark.api


class TestQueryKnowledgeBase:
    def test_success(self, client):
        kb_id = uuid.uuid4()
        mock_result = {
            "question": "什么是RAG？",
            "answer": "RAG是检索增强生成技术。",
            "citations": [
                {
                    "index": 1,
                    "chunk_id": str(uuid.uuid4()),
                    "document_id": str(uuid.uuid4()),
                    "content": "RAG stands for Retrieval-Augmented Generation.",
                    "page_number": 1,
                    "filename": "intro.pdf",
                    "score": 0.92,
                }
            ],
        }
        with patch("app.services.qa.ask", new_callable=AsyncMock, return_value=mock_result):
            resp = client.post(
                f"/api/v1/knowledge-bases/{kb_id}/query",
                json={"question": "什么是RAG？"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["question"] == "什么是RAG？"
        assert data["answer"] == "RAG是检索增强生成技术。"
        assert len(data["citations"]) == 1
        assert data["citations"][0]["filename"] == "intro.pdf"

    def test_empty_question_rejected(self, client):
        kb_id = uuid.uuid4()
        resp = client.post(
            f"/api/v1/knowledge-bases/{kb_id}/query",
            json={"question": ""},
        )
        assert resp.status_code == 422

    def test_missing_question_rejected(self, client):
        kb_id = uuid.uuid4()
        resp = client.post(
            f"/api/v1/knowledge-bases/{kb_id}/query",
            json={},
        )
        assert resp.status_code == 422

    def test_custom_top_k(self, client):
        kb_id = uuid.uuid4()
        mock_result = {"question": "q", "answer": "a", "citations": []}
        with patch("app.services.qa.ask", new_callable=AsyncMock, return_value=mock_result) as mock_ask:
            resp = client.post(
                f"/api/v1/knowledge-bases/{kb_id}/query",
                json={"question": "test", "top_k": 10},
            )
        assert resp.status_code == 200
        # Verify top_k was passed through
        call_args = mock_ask.call_args
        assert call_args.kwargs.get("top_k") == 10 or call_args[0][-1] == 10

    def test_top_k_out_of_range(self, client):
        kb_id = uuid.uuid4()
        resp = client.post(
            f"/api/v1/knowledge-bases/{kb_id}/query",
            json={"question": "test", "top_k": 50},
        )
        assert resp.status_code == 422

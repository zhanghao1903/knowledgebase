"""API tests for global error handling — verify uniform error response format."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

pytestmark = pytest.mark.api


class TestErrorResponses:
    def test_404_format(self, client):
        """NotFoundError should return structured JSON."""
        from app.core.exceptions import NotFoundError
        fake_id = uuid.uuid4()
        with patch("app.services.knowledge_base.get_knowledge_base", new_callable=AsyncMock, side_effect=NotFoundError("KnowledgeBase", fake_id)):
            resp = client.get(f"/api/v1/knowledge-bases/{fake_id}")
        assert resp.status_code == 404
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == 404
        assert "not found" in data["error"]["message"]

    def test_422_format(self, client):
        """Validation errors should return structured JSON with field details."""
        resp = client.post("/api/v1/knowledge-bases", json={"name": ""})
        assert resp.status_code == 422
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == 422
        assert "details" in data["error"]
        assert isinstance(data["error"]["details"], list)
        assert len(data["error"]["details"]) > 0

    def test_422_missing_field(self, client):
        resp = client.post("/api/v1/knowledge-bases", json={})
        assert resp.status_code == 422
        data = resp.json()
        assert data["error"]["code"] == 422

    def test_500_format(self, client):
        """Unhandled exceptions should return generic 500 without leaking details."""
        with patch("app.services.knowledge_base.list_knowledge_bases", new_callable=AsyncMock, side_effect=RuntimeError("unexpected")):
            resp = client.get("/api/v1/knowledge-bases")
        assert resp.status_code == 500
        data = resp.json()
        assert data["error"]["code"] == 500
        assert "unexpected" not in data["error"]["message"]  # no leak

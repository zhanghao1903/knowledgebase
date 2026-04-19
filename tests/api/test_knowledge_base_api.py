"""API tests for Knowledge Base CRUD endpoints."""
from unittest.mock import AsyncMock, patch

import pytest

from tests.api.conftest import make_kb

pytestmark = pytest.mark.api

BASE = "/api/v1/knowledge-bases"


class TestCreateKnowledgeBase:
    def test_success(self, client):
        kb = make_kb(name="新知识库")
        with patch("app.services.knowledge_base.create_knowledge_base", new_callable=AsyncMock, return_value=kb):
            resp = client.post(BASE, json={"name": "新知识库", "description": "描述"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "新知识库"
        assert "id" in data
        assert "created_at" in data

    def test_empty_name_rejected(self, client):
        resp = client.post(BASE, json={"name": ""})
        assert resp.status_code == 422

    def test_missing_name_rejected(self, client):
        resp = client.post(BASE, json={})
        assert resp.status_code == 422


class TestListKnowledgeBases:
    def test_success(self, client):
        kbs = [make_kb(name=f"KB_{i}") for i in range(3)]
        with patch("app.services.knowledge_base.list_knowledge_bases", new_callable=AsyncMock, return_value=(kbs, 3)):
            resp = client.get(BASE)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_pagination_params(self, client):
        with patch("app.services.knowledge_base.list_knowledge_bases", new_callable=AsyncMock, return_value=([], 0)):
            resp = client.get(BASE, params={"offset": 10, "limit": 5})
        assert resp.status_code == 200

    def test_invalid_limit(self, client):
        resp = client.get(BASE, params={"limit": 0})
        assert resp.status_code == 422


class TestGetKnowledgeBase:
    def test_success(self, client):
        kb = make_kb()
        with patch("app.services.knowledge_base.get_knowledge_base", new_callable=AsyncMock, return_value=kb):
            resp = client.get(f"{BASE}/{kb.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == str(kb.id)

    def test_not_found(self, client):
        from app.core.exceptions import NotFoundError
        with patch("app.services.knowledge_base.get_knowledge_base", new_callable=AsyncMock, side_effect=NotFoundError("KnowledgeBase", "fake-id")):
            resp = client.get(f"{BASE}/00000000-0000-0000-0000-000000000001")
        assert resp.status_code == 404


class TestUpdateKnowledgeBase:
    def test_success(self, client):
        kb = make_kb(name="更新后的名称")
        with patch("app.services.knowledge_base.update_knowledge_base", new_callable=AsyncMock, return_value=kb):
            resp = client.patch(f"{BASE}/{kb.id}", json={"name": "更新后的名称"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "更新后的名称"


class TestDeleteKnowledgeBase:
    def test_success(self, client):
        import uuid
        kb_id = uuid.uuid4()
        with patch("app.services.knowledge_base.delete_knowledge_base", new_callable=AsyncMock):
            resp = client.delete(f"{BASE}/{kb_id}")
        assert resp.status_code == 204

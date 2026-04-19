"""API tests for Task query endpoints."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.models.task import TaskStatus
from tests.api.conftest import make_task

pytestmark = pytest.mark.api

BASE = "/api/v1/tasks"


class TestGetTask:
    def test_success(self, client):
        task = make_task(status=TaskStatus.SUCCESS)
        with patch("app.services.task.get_task", new_callable=AsyncMock, return_value=task):
            resp = client.get(f"{BASE}/{task.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(task.id)
        assert data["status"] == "success"

    def test_not_found(self, client):
        from app.core.exceptions import NotFoundError
        tid = uuid.uuid4()
        with patch("app.services.task.get_task", new_callable=AsyncMock, side_effect=NotFoundError("Task", tid)):
            resp = client.get(f"{BASE}/{tid}")
        assert resp.status_code == 404


class TestListTasks:
    def test_success(self, client):
        tasks = [make_task() for _ in range(3)]
        with patch("app.services.task.list_tasks", new_callable=AsyncMock, return_value=(tasks, 3)):
            resp = client.get(BASE)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_filter_by_status(self, client):
        tasks = [make_task(status=TaskStatus.FAILED)]
        with patch("app.services.task.list_tasks", new_callable=AsyncMock, return_value=(tasks, 1)):
            resp = client.get(BASE, params={"status": "failed"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_filter_by_document_id(self, client):
        doc_id = uuid.uuid4()
        tasks = [make_task(document_id=doc_id)]
        with patch("app.services.task.list_tasks", new_callable=AsyncMock, return_value=(tasks, 1)):
            resp = client.get(BASE, params={"document_id": str(doc_id)})
        assert resp.status_code == 200

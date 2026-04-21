"""API tests for URL document endpoints."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import (
    InvalidURLError,
    NotFoundError,
    UnsupportedSourceOperationError,
    URLFetchError,
)
from app.models.document import FileType, SourceType
from tests.api.conftest import make_document, make_task

pytestmark = pytest.mark.api


# ── POST /knowledge-bases/{kb_id}/documents/url ──────────────────────────

class TestUploadURLDocument:
    def test_success(self, client):
        kb_id = uuid.uuid4()
        doc = make_document(
            kb_id=kb_id,
            filename="How to write a KB",
            source_type=SourceType.URL,
            source_url="https://example.com/article",
            file_type=FileType.HTML,
        )
        task = make_task(document_id=doc.id)
        with patch(
            "app.services.document.upload_url_document",
            new_callable=AsyncMock,
            return_value=(doc, task),
        ):
            resp = client.post(
                f"/api/v1/knowledge-bases/{kb_id}/documents/url",
                json={"url": "https://example.com/article"},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["document"]["source_type"] == "url"
        assert data["document"]["source_url"] == "https://example.com/article"
        assert data["document"]["file_type"] == "html"
        assert "task_id" in data

    def test_empty_url_rejected(self, client):
        kb_id = uuid.uuid4()
        resp = client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/url",
            json={"url": ""},
        )
        assert resp.status_code == 422

    def test_missing_url_rejected(self, client):
        kb_id = uuid.uuid4()
        resp = client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/url",
            json={},
        )
        assert resp.status_code == 422

    def test_invalid_url_returns_400(self, client):
        kb_id = uuid.uuid4()
        with patch(
            "app.services.document.upload_url_document",
            new_callable=AsyncMock,
            side_effect=InvalidURLError("Only http/https URLs are allowed"),
        ):
            resp = client.post(
                f"/api/v1/knowledge-bases/{kb_id}/documents/url",
                json={"url": "file:///etc/passwd"},
            )
        assert resp.status_code == 400
        assert "Invalid URL" in resp.json()["error"]["message"]

    def test_fetch_failure_returns_400(self, client):
        kb_id = uuid.uuid4()
        with patch(
            "app.services.document.upload_url_document",
            new_callable=AsyncMock,
            side_effect=URLFetchError("HTTP 500"),
        ):
            resp = client.post(
                f"/api/v1/knowledge-bases/{kb_id}/documents/url",
                json={"url": "https://example.com/down"},
            )
        assert resp.status_code == 400
        assert "Failed to fetch URL" in resp.json()["error"]["message"]

    def test_kb_not_found(self, client):
        kb_id = uuid.uuid4()
        with patch(
            "app.services.document.upload_url_document",
            new_callable=AsyncMock,
            side_effect=NotFoundError("KnowledgeBase", kb_id),
        ):
            resp = client.post(
                f"/api/v1/knowledge-bases/{kb_id}/documents/url",
                json={"url": "https://example.com/"},
            )
        assert resp.status_code == 404


# ── POST /documents/{id}/recrawl ─────────────────────────────────────────

class TestRecrawlDocument:
    def test_changed_returns_new_task(self, client):
        doc = make_document(
            source_type=SourceType.URL,
            source_url="https://example.com/article",
            file_type=FileType.HTML,
        )
        task = make_task(document_id=doc.id)
        with patch(
            "app.services.document.recrawl_url_document",
            new_callable=AsyncMock,
            return_value=(doc, task, True),
        ):
            resp = client.post(f"/api/v1/documents/{doc.id}/recrawl")
        assert resp.status_code == 200
        data = resp.json()
        assert data["changed"] is True
        assert data["task_id"] == str(task.id)
        assert "new version" in data["message"]

    def test_unchanged_returns_no_task(self, client):
        doc = make_document(
            source_type=SourceType.URL,
            source_url="https://example.com/article",
            file_type=FileType.HTML,
        )
        with patch(
            "app.services.document.recrawl_url_document",
            new_callable=AsyncMock,
            return_value=(doc, None, False),
        ):
            resp = client.post(f"/api/v1/documents/{doc.id}/recrawl")
        assert resp.status_code == 200
        data = resp.json()
        assert data["changed"] is False
        assert data["task_id"] is None
        assert "unchanged" in data["message"]

    def test_file_document_rejected(self, client):
        doc = make_document()  # source_type=FILE by default
        with patch(
            "app.services.document.recrawl_url_document",
            new_callable=AsyncMock,
            side_effect=UnsupportedSourceOperationError(
                "Recrawl is only supported for URL-sourced documents."
            ),
        ):
            resp = client.post(f"/api/v1/documents/{doc.id}/recrawl")
        assert resp.status_code == 400
        assert "URL-sourced" in resp.json()["error"]["message"]

    def test_not_found(self, client):
        doc_id = uuid.uuid4()
        with patch(
            "app.services.document.recrawl_url_document",
            new_callable=AsyncMock,
            side_effect=NotFoundError("Document", doc_id),
        ):
            resp = client.post(f"/api/v1/documents/{doc_id}/recrawl")
        assert resp.status_code == 404

    def test_fetch_failure_during_recrawl(self, client):
        doc_id = uuid.uuid4()
        with patch(
            "app.services.document.recrawl_url_document",
            new_callable=AsyncMock,
            side_effect=URLFetchError("Request timed out"),
        ):
            resp = client.post(f"/api/v1/documents/{doc_id}/recrawl")
        assert resp.status_code == 400


# ── Reupload blocks URL documents ────────────────────────────────────────

class TestReuploadBlocksURLDocuments:
    def test_url_document_reupload_rejected(self, client):
        doc = make_document(
            source_type=SourceType.URL,
            source_url="https://example.com/x",
            file_type=FileType.HTML,
        )
        with patch(
            "app.services.document.reupload_document",
            new_callable=AsyncMock,
            side_effect=UnsupportedSourceOperationError(
                "This document was ingested from a URL. Use POST "
                "/documents/{id}/recrawl to refresh it."
            ),
        ):
            import io

            resp = client.put(
                f"/api/v1/documents/{doc.id}/reupload",
                files={"file": ("x.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
            )
        assert resp.status_code == 400
        assert "URL" in resp.json()["error"]["message"]

"""API tests for Document management endpoints."""
import io
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.models.document import DocumentStatus
from tests.api.conftest import make_document, make_task

pytestmark = pytest.mark.api


class TestUploadDocument:
    def test_success(self, client):
        kb_id = uuid.uuid4()
        doc = make_document(kb_id=kb_id, filename="report.pdf")
        task = make_task(document_id=doc.id)
        with patch("app.services.document.upload_document", new_callable=AsyncMock, return_value=(doc, task)):
            resp = client.post(
                f"/api/v1/knowledge-bases/{kb_id}/documents",
                files={"file": ("report.pdf", io.BytesIO(b"fake pdf"), "application/pdf")},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["document"]["filename"] == "report.pdf"
        assert "task_id" in data

    def test_no_file_rejected(self, client):
        kb_id = uuid.uuid4()
        resp = client.post(f"/api/v1/knowledge-bases/{kb_id}/documents")
        assert resp.status_code == 422


class TestListDocuments:
    def test_success(self, client):
        kb_id = uuid.uuid4()
        docs = [make_document(kb_id=kb_id, filename=f"doc_{i}.pdf") for i in range(2)]
        with patch("app.services.document.list_documents", new_callable=AsyncMock, return_value=(docs, 2)):
            resp = client.get(f"/api/v1/knowledge-bases/{kb_id}/documents")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2


class TestGetDocument:
    def test_success(self, client):
        doc = make_document()
        with patch("app.services.document.get_document", new_callable=AsyncMock, return_value=doc):
            resp = client.get(f"/api/v1/documents/{doc.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == str(doc.id)

    def test_not_found(self, client):
        from app.core.exceptions import NotFoundError
        doc_id = uuid.uuid4()
        with patch("app.services.document.get_document", new_callable=AsyncMock, side_effect=NotFoundError("Document", doc_id)):
            resp = client.get(f"/api/v1/documents/{doc_id}")
        assert resp.status_code == 404


class TestGetDocumentVersions:
    def test_success(self, client):
        from app.models.document import DocumentVersion
        from datetime import datetime, timezone

        doc_id = uuid.uuid4()
        v = DocumentVersion(
            id=uuid.uuid4(),
            document_id=doc_id,
            version_number=1,
            file_path="/tmp/v1_test.pdf",
            file_size=1024,
            created_at=datetime.now(timezone.utc),
        )

        with patch("app.services.document.get_document_versions", new_callable=AsyncMock, return_value=[v]):
            resp = client.get(f"/api/v1/documents/{doc_id}/versions")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["version_number"] == 1


class TestReuploadDocument:
    def test_success(self, client):
        doc = make_document(filename="updated.pdf")
        task = make_task(document_id=doc.id)
        with patch("app.services.document.reupload_document", new_callable=AsyncMock, return_value=(doc, task)):
            resp = client.put(
                f"/api/v1/documents/{doc.id}/reupload",
                files={"file": ("updated.pdf", io.BytesIO(b"new content"), "application/pdf")},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        assert data["document"]["filename"] == "updated.pdf"

    def test_not_found(self, client):
        from app.core.exceptions import NotFoundError
        doc_id = uuid.uuid4()
        with patch("app.services.document.reupload_document", new_callable=AsyncMock, side_effect=NotFoundError("Document", doc_id)):
            resp = client.put(
                f"/api/v1/documents/{doc_id}/reupload",
                files={"file": ("test.pdf", io.BytesIO(b"data"), "application/pdf")},
            )
        assert resp.status_code == 404


class TestDeleteDocument:
    def test_success(self, client):
        doc_id = uuid.uuid4()
        with patch("app.services.document.delete_document", new_callable=AsyncMock):
            resp = client.delete(f"/api/v1/documents/{doc_id}")
        assert resp.status_code == 204

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.document import DocumentStatus, FileType


class DocumentResponse(BaseModel):
    id: uuid.UUID
    knowledge_base_id: uuid.UUID
    filename: str
    file_type: FileType
    file_size: int
    status: DocumentStatus
    current_version: int
    chunk_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentList(BaseModel):
    items: list[DocumentResponse]
    total: int


class DocumentVersionResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    version_number: int
    file_size: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    task_id: uuid.UUID
    message: str = "Document uploaded, processing started"

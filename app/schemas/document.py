import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.document import DocumentStatus, FileType, SourceType


class DocumentResponse(BaseModel):
    id: uuid.UUID
    knowledge_base_id: uuid.UUID
    filename: str
    file_type: FileType
    file_size: int
    source_type: SourceType
    source_url: str | None = None
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
    source_url: str | None = None
    content_hash: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    task_id: uuid.UUID
    message: str = "Document uploaded, processing started"


class DocumentURLCreateRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)


class DocumentRecrawlResponse(BaseModel):
    document: DocumentResponse
    task_id: uuid.UUID | None = None
    changed: bool
    message: str

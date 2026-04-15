import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["技术文档库"])
    description: str | None = Field(None, examples=["存放内部技术文档"])


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None


class KnowledgeBaseResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    document_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeBaseList(BaseModel):
    items: list[KnowledgeBaseResponse]
    total: int

import uuid
from datetime import datetime

from pydantic import BaseModel


class ChunkResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    version_number: int
    content: str
    chunk_index: int
    page_number: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChunkList(BaseModel):
    items: list[ChunkResponse]
    total: int

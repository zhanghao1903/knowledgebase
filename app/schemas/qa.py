import uuid

from pydantic import BaseModel, Field

from app.config import settings


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    top_k: int = Field(
        default=settings.RETRIEVAL_TOP_K,
        ge=1,
        le=20,
        description="检索返回的最相关片段数",
    )


class Citation(BaseModel):
    index: int
    chunk_id: str
    document_id: str
    content: str
    page_number: int | None
    filename: str
    score: float


class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation]

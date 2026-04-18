import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.qa import QueryRequest, QueryResponse
from app.services import qa as qa_service

router = APIRouter(tags=["Q&A"])


@router.post(
    "/knowledge-bases/{kb_id}/query",
    response_model=QueryResponse,
)
async def query_knowledge_base(
    kb_id: uuid.UUID,
    req: QueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """对指定知识库提问，返回基于检索的 AI 回答及引用片段"""
    result = await qa_service.ask(db, kb_id, req.question, top_k=req.top_k)
    return QueryResponse(**result)

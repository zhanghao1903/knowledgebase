import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseList,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)
from app.services import knowledge_base as kb_service

router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge Base"])


@router.post("", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(
    data: KnowledgeBaseCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建知识库"""
    return await kb_service.create_knowledge_base(db, data)


@router.get("", response_model=KnowledgeBaseList)
async def list_knowledge_bases(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取知识库列表"""
    items, total = await kb_service.list_knowledge_bases(db, offset, limit)
    return KnowledgeBaseList(items=items, total=total)


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """获取单个知识库详情"""
    return await kb_service.get_knowledge_base(db, kb_id)


@router.patch("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: uuid.UUID,
    data: KnowledgeBaseUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新知识库信息"""
    return await kb_service.update_knowledge_base(db, kb_id, data)


@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(
    kb_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """删除知识库及其所有文档"""
    await kb_service.delete_knowledge_base(db, kb_id)

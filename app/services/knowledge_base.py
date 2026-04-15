import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.knowledge_base import KnowledgeBase
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate


async def create_knowledge_base(db: AsyncSession, data: KnowledgeBaseCreate) -> KnowledgeBase:
    kb = KnowledgeBase(name=data.name, description=data.description)
    db.add(kb)
    await db.flush()
    await db.refresh(kb)
    return kb


async def get_knowledge_base(db: AsyncSession, kb_id: uuid.UUID) -> KnowledgeBase:
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        raise NotFoundError("KnowledgeBase", kb_id)
    return kb


async def list_knowledge_bases(
    db: AsyncSession, offset: int = 0, limit: int = 20
) -> tuple[list[KnowledgeBase], int]:
    count_result = await db.execute(select(func.count(KnowledgeBase.id)))
    total = count_result.scalar()

    result = await db.execute(
        select(KnowledgeBase)
        .order_by(KnowledgeBase.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list(result.scalars().all())
    return items, total


async def update_knowledge_base(
    db: AsyncSession, kb_id: uuid.UUID, data: KnowledgeBaseUpdate
) -> KnowledgeBase:
    kb = await get_knowledge_base(db, kb_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(kb, field, value)
    await db.flush()
    await db.refresh(kb)
    return kb


async def delete_knowledge_base(db: AsyncSession, kb_id: uuid.UUID) -> None:
    kb = await get_knowledge_base(db, kb_id)
    await db.delete(kb)
    await db.flush()

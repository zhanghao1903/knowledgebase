import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.task import Task, TaskStatus


async def get_task(db: AsyncSession, task_id: uuid.UUID) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundError("Task", task_id)
    return task


async def list_tasks(
    db: AsyncSession,
    document_id: uuid.UUID | None = None,
    status: TaskStatus | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Task], int]:
    query = select(Task)
    count_query = select(func.count(Task.id))

    if document_id:
        query = query.where(Task.document_id == document_id)
        count_query = count_query.where(Task.document_id == document_id)
    if status:
        query = query.where(Task.status == status)
        count_query = count_query.where(Task.status == status)

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    result = await db.execute(
        query.order_by(Task.created_at.desc()).offset(offset).limit(limit)
    )
    items = list(result.scalars().all())
    return items, total

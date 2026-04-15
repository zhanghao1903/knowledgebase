import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.task import TaskStatus
from app.schemas.task import TaskList, TaskResponse
from app.services import task as task_service

router = APIRouter(prefix="/tasks", tags=["Task"])


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """查询单个任务状态"""
    return await task_service.get_task(db, task_id)


@router.get("", response_model=TaskList)
async def list_tasks(
    document_id: uuid.UUID | None = Query(None),
    status: TaskStatus | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """查询任务列表，支持按文档 ID 和状态筛选"""
    items, total = await task_service.list_tasks(db, document_id, status, offset, limit)
    return TaskList(items=items, total=total)

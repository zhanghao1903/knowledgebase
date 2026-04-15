import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.task import TaskStatus, TaskType


class TaskResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    task_type: TaskType
    status: TaskStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class TaskList(BaseModel):
    items: list[TaskResponse]
    total: int

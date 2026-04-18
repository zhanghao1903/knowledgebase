"""Background worker that polls for pending ingest tasks and executes them.

Runs as an asyncio task within the FastAPI process — no external
message queue needed. Suitable for a single-instance prototype.
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.database import async_session
from app.models.task import Task, TaskStatus, TaskType
from app.services.ingest import run_ingest

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 3


async def worker_loop() -> None:
    """Continuously poll for and process pending tasks."""
    logger.info("Worker started — polling every %ds", POLL_INTERVAL_SECONDS)

    while True:
        try:
            await _process_next_task()
        except asyncio.CancelledError:
            logger.info("Worker shutting down")
            break
        except Exception:
            logger.exception("Unexpected error in worker loop")

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def _process_next_task() -> None:
    """Find and execute one pending task (if any)."""
    async with async_session() as db:
        try:
            # Pick the oldest pending ingest task
            result = await db.execute(
                select(Task)
                .where(Task.status == TaskStatus.PENDING)
                .where(Task.task_type == TaskType.DOCUMENT_INGEST)
                .order_by(Task.created_at.asc())
                .limit(1)
            )
            task = result.scalar_one_or_none()

            if task is None:
                return

            logger.info("Processing task %s (document=%s)", task.id, task.document_id)
            await run_ingest(task.id, db)
            await db.commit()
            logger.info("Task %s completed", task.id)

        except Exception:
            await db.rollback()
            logger.exception("Task processing failed — transaction rolled back")

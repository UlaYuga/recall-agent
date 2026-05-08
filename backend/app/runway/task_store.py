"""CRUD helpers for the RunwayTask persistence table.

All functions accept an open SQLModel Session so the caller controls
transaction boundaries.  No Runway SDK calls are made here.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from sqlmodel import Session, select

from app.models import RunwayTask

TaskKind = Literal["text_to_image", "image_to_video", "tts"]

# Runway task statuses aligned to the SDK's task lifecycle.
TaskStatus = Literal["pending", "throttled", "running", "succeeded", "failed", "cancelled"]


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def create_task(
    session: Session,
    *,
    task_id: str,
    campaign_id: str,
    kind: TaskKind,
    model: str | None = None,
    scene_id: str | None = None,
    credits_estimated: int | None = None,
    status: str = "pending",
) -> RunwayTask:
    """Insert a new RunwayTask row and return the persisted instance."""
    task = RunwayTask(
        task_id=task_id,
        campaign_id=campaign_id,
        kind=kind,
        model=model,
        scene_id=scene_id,
        credits_estimated=credits_estimated,
        status=status,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


def get_task(session: Session, task_id: str) -> RunwayTask | None:
    """Return the RunwayTask with the given Runway task_id, or None."""
    return session.exec(
        select(RunwayTask).where(RunwayTask.task_id == task_id)
    ).first()


def list_tasks(
    session: Session,
    campaign_id: str,
    *,
    kind: str | None = None,
) -> list[RunwayTask]:
    """Return RunwayTask rows for *campaign_id*, optionally filtered by *kind*."""
    stmt = select(RunwayTask).where(RunwayTask.campaign_id == campaign_id)
    if kind is not None:
        stmt = stmt.where(RunwayTask.kind == kind)
    return list(session.exec(stmt).all())


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def update_task(
    session: Session,
    task_id: str,
    *,
    status: str | None = None,
    output_url: str | None = None,
    failure_code: str | None = None,
    retry_count: int | None = None,
) -> RunwayTask | None:
    """Update mutable fields on an existing RunwayTask.

    Only keyword arguments that are not None are applied; pass an explicit
    value to change a field.  Sets updated_at to the current UTC time.

    Returns the updated row, or None if *task_id* is not found.
    """
    task = get_task(session, task_id)
    if task is None:
        return None
    if status is not None:
        task.status = status
    if output_url is not None:
        task.output_url = output_url
    if failure_code is not None:
        task.failure_code = failure_code
    if retry_count is not None:
        task.retry_count = retry_count
    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

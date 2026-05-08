"""Video generation API.

POST /video/generate          — start Runway pipeline for an approved campaign
GET  /video/status/{task_id}  — poll status by campaign_id or RunwayTask.task_id

Contract (from TECH_SPEC / T-21-VIDEO-CONTRACT decision):
  POST /video/generate   body {"campaign_id": "..."}
  GET  /video/status/{task_id}

The pipeline runs in a FastAPI BackgroundTask so the POST returns immediately
with a job identifier.  Clients poll GET /video/status/{campaign_id} for
aggregate status, or GET /video/status/{runway_task_id} for a sub-task.

Injectable boundary
-------------------
_pipeline_fn is a module-level variable.  Tests patch it with::

    monkeypatch.setattr("app.api.video._pipeline_fn", mock_fn)

to avoid real Runway calls and ffmpeg execution.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Callable

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, create_engine, select

from app.config import settings
from app.db import get_session
from app.models import Campaign, CampaignStatus, RunwayTask, VideoAsset
from app.runway.client import RunwayClient
from app.runway.task_store import list_tasks
from app.runway.video_pipeline import PipelineResult, run_video_pipeline

router = APIRouter()

# ---------------------------------------------------------------------------
# Injectable pipeline boundary — replace in tests via patch
# ---------------------------------------------------------------------------

PipelineFn = Callable[..., PipelineResult]

_pipeline_fn: PipelineFn = run_video_pipeline


# ---------------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------------


class GenerateRequest(BaseModel):
    campaign_id: str


# ---------------------------------------------------------------------------
# Internal helpers (also used directly in unit tests)
# ---------------------------------------------------------------------------


def _get_campaign_or_404(session: Session, campaign_id: str) -> Campaign:
    campaign = session.exec(
        select(Campaign).where(Campaign.campaign_id == campaign_id)
    ).first()
    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign {campaign_id!r} not found",
        )
    return campaign  # type: ignore[return-value]


def _ensure_video_asset(
    session: Session,
    campaign_id: str,
    status: str = "queued",
) -> VideoAsset:
    """Create a new VideoAsset or reset an existing one to *status*."""
    asset = session.exec(
        select(VideoAsset).where(VideoAsset.campaign_id == campaign_id)
    ).first()
    if asset is None:
        asset = VideoAsset(campaign_id=campaign_id, status=status)
    else:
        asset.status = status
        asset.video_url = None
        asset.poster_url = None
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset  # type: ignore[return-value]


def _apply_pipeline_result(
    session: Session,
    campaign: Campaign,
    result: PipelineResult,
) -> None:
    """Persist a successful PipelineResult — update VideoAsset and Campaign."""
    asset = session.exec(
        select(VideoAsset).where(VideoAsset.campaign_id == campaign.campaign_id)
    ).first()
    if asset is None:
        asset = VideoAsset(campaign_id=campaign.campaign_id)
    asset.video_url = result.video_path
    asset.poster_url = result.poster_path
    asset.status = "ready"
    session.add(asset)

    campaign.status = CampaignStatus.ready
    campaign.updated_at = datetime.now(timezone.utc)
    session.add(campaign)
    session.commit()


def _apply_pipeline_failure(session: Session, campaign: Campaign) -> None:
    """Mark VideoAsset as failed and Campaign as generation_failed."""
    asset = session.exec(
        select(VideoAsset).where(VideoAsset.campaign_id == campaign.campaign_id)
    ).first()
    if asset is not None:
        asset.status = "failed"
        session.add(asset)

    campaign.status = CampaignStatus.generation_failed
    campaign.updated_at = datetime.now(timezone.utc)
    session.add(campaign)
    session.commit()


# ---------------------------------------------------------------------------
# Background task
# ---------------------------------------------------------------------------


def _generation_background_task(
    campaign_id: str,
    db_url: str,
    storage_dir: str,
    pipeline_fn: PipelineFn,
) -> None:
    """Open a fresh DB session, instantiate RunwayClient, run the pipeline.

    This runs AFTER the HTTP response is returned, so it must open its own
    SQLModel Session.  It must NOT share the request-scoped session.

    Errors are caught and persisted as generation_failed — they are never
    surfaced to the caller (who is polling status).
    """
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    with Session(engine) as session:
        campaign = session.exec(
            select(Campaign).where(Campaign.campaign_id == campaign_id)
        ).first()
        if campaign is None:
            return  # Campaign was deleted between request and bg task — ignore.

        # Instantiate client — raises RunwayConfigError if env var is missing.
        try:
            client = RunwayClient()
        except Exception:
            _apply_pipeline_failure(session, campaign)
            return

        # Run the pipeline — raises RunwayTaskError on sub-task failure.
        try:
            result = pipeline_fn(
                campaign,
                client=client,
                session=session,
                storage_dir=storage_dir,
            )
        except Exception:
            _apply_pipeline_failure(session, campaign)
            return

        _apply_pipeline_result(session, campaign, result)


# ---------------------------------------------------------------------------
# POST /video/generate
# ---------------------------------------------------------------------------


@router.post("/generate")
def generate(
    body: GenerateRequest,
    background_tasks: BackgroundTasks,
    session: Annotated[Session, Depends(get_session)],
) -> dict[str, Any]:
    """Start Runway video generation for an approved campaign.

    Returns immediately with ``campaign_id`` as the polling identifier.
    Poll ``GET /video/status/{campaign_id}`` to track progress.

    Raises
    ------
    404  Campaign not found.
    409  Campaign is not in ``approved`` status.
    422  Campaign has no ``script_json``.
    """
    campaign = _get_campaign_or_404(session, body.campaign_id)

    if campaign.status != CampaignStatus.approved:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Campaign must be in 'approved' status to generate video "
                f"(current: {campaign.status.value})"
            ),
        )

    if not campaign.script_json:
        raise HTTPException(
            status_code=422,
            detail=(
                "Campaign has no script_json — run /agent/decide or "
                "/approval/{id}/regenerate-script first"
            ),
        )

    # Set up the VideoAsset row as queued (resets any prior attempt).
    _ensure_video_asset(session, body.campaign_id, status="queued")

    # Transition campaign to generating.
    campaign.status = CampaignStatus.generating
    campaign.updated_at = datetime.now(timezone.utc)
    session.add(campaign)
    session.commit()

    # Schedule the pipeline — runs after this response is returned.
    background_tasks.add_task(
        _generation_background_task,
        campaign_id=body.campaign_id,
        db_url=settings.database_url,
        storage_dir=settings.storage_dir,
        pipeline_fn=_pipeline_fn,
    )

    return {
        "campaign_id": body.campaign_id,
        "status": "queued",
    }


# ---------------------------------------------------------------------------
# GET /video/status/{task_id}
# ---------------------------------------------------------------------------


@router.get("/status/{task_id}")
def status(
    task_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> dict[str, Any]:
    """Return video generation status.

    ``task_id`` is interpreted as follows:

    1. If it matches a ``RunwayTask.task_id`` in task_store → return that
       sub-task's status (kind, model, output_url, failure_code).
    2. If it matches a ``VideoAsset.campaign_id`` → return the aggregate
       video status (queued | generating | ready | failed) plus
       ``video_url`` / ``poster_url`` when available, and all associated
       Runway sub-task IDs.
    3. Otherwise → 404.

    Raises
    ------
    404  No task or campaign matches *task_id*.
    """
    # 1. Check RunwayTask sub-task table first.
    runway_task = session.exec(
        select(RunwayTask).where(RunwayTask.task_id == task_id)
    ).first()
    if runway_task is not None:
        return {
            "task_id": task_id,
            "kind": runway_task.kind,
            "model": runway_task.model,
            "status": runway_task.status,
            "campaign_id": runway_task.campaign_id,
            "output_url": runway_task.output_url,
            "failure_code": runway_task.failure_code,
            "created_at": runway_task.created_at.isoformat() if runway_task.created_at else None,
            "updated_at": runway_task.updated_at.isoformat() if runway_task.updated_at else None,
        }

    # 2. Fall back to VideoAsset look-up by campaign_id.
    asset = session.exec(
        select(VideoAsset).where(VideoAsset.campaign_id == task_id)
    ).first()
    if asset is not None:
        payload: dict[str, Any] = {
            "campaign_id": task_id,
            "status": asset.status,
        }
        if asset.video_url:
            payload["video_url"] = asset.video_url
        if asset.poster_url:
            payload["poster_url"] = asset.poster_url
        # Include all sub-task IDs so callers can drill into individual tasks.
        sub_tasks = list_tasks(session, task_id)
        payload["runway_task_ids"] = [t.task_id for t in sub_tasks]
        return payload

    raise HTTPException(
        status_code=404,
        detail=f"No task or campaign found for id {task_id!r}",
    )

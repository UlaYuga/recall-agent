"""Tests for app.api.video — POST /video/generate and GET /video/status.

All RunwayClient calls and pipeline execution are mocked.
No real Runway calls, no ffmpeg execution.

Test structure
--------------
TestGenerateEndpoint   — POST /video/generate contract + validation
TestStatusEndpoint     — GET /video/status/{task_id} lookup paths
TestPipelineHelpers    — unit tests for _apply_pipeline_result /
                         _apply_pipeline_failure called with a live session
"""
from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db import get_session
from app.main import app
from app.models import Campaign, CampaignStatus, RunwayTask, VideoAsset
from app.runway.video_pipeline import PipelineResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(name="engine")
def engine_fixture():
    _engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(_engine)
    yield _engine


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_campaign(
    session: Session,
    campaign_id: str = "cmp_test",
    status: CampaignStatus = CampaignStatus.approved,
    script_json: str | None = '{"scenes": [{"id": 1, "visual_brief": "abstract"}]}',
) -> Campaign:
    c = Campaign(
        campaign_id=campaign_id,
        player_id="p_001",
        cohort="lapsed_loyal",
        status=status,
        script_json=script_json,
    )
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


def _make_video_asset(
    session: Session,
    campaign_id: str,
    status: str = "queued",
    video_url: str | None = None,
    poster_url: str | None = None,
) -> VideoAsset:
    a = VideoAsset(
        campaign_id=campaign_id,
        status=status,
        video_url=video_url,
        poster_url=poster_url,
    )
    session.add(a)
    session.commit()
    session.refresh(a)
    return a


def _make_runway_task(
    session: Session,
    task_id: str,
    campaign_id: str,
    kind: str = "image_to_video",
    status: str = "succeeded",
    output_url: str | None = "https://runway.example.com/clip.mp4",
) -> RunwayTask:
    t = RunwayTask(
        task_id=task_id,
        campaign_id=campaign_id,
        kind=kind,
        status=status,
        output_url=output_url,
    )
    session.add(t)
    session.commit()
    session.refresh(t)
    return t


def _noop_bg_task(*args: Any, **kwargs: Any) -> None:
    """Background task stub — does nothing; used to isolate endpoint tests."""


# ---------------------------------------------------------------------------
# TestGenerateEndpoint
# ---------------------------------------------------------------------------


class TestGenerateEndpoint:
    """POST /video/generate"""

    def test_returns_campaign_id_and_queued_status(self, client, session):
        _make_campaign(session)
        with patch("app.api.video._generation_background_task", _noop_bg_task):
            resp = client.post("/video/generate", json={"campaign_id": "cmp_test"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["campaign_id"] == "cmp_test"
        assert body["status"] == "queued"

    def test_campaign_not_found_returns_404(self, client):
        resp = client.post("/video/generate", json={"campaign_id": "no_such"})
        assert resp.status_code == 404

    def test_non_approved_status_returns_409(self, client, session):
        _make_campaign(session, status=CampaignStatus.draft)
        resp = client.post("/video/generate", json={"campaign_id": "cmp_test"})
        assert resp.status_code == 409
        assert "approved" in resp.json()["detail"].lower()

    def test_generating_status_returns_409(self, client, session):
        _make_campaign(session, status=CampaignStatus.generating)
        resp = client.post("/video/generate", json={"campaign_id": "cmp_test"})
        assert resp.status_code == 409

    def test_already_ready_returns_409(self, client, session):
        _make_campaign(session, status=CampaignStatus.ready)
        resp = client.post("/video/generate", json={"campaign_id": "cmp_test"})
        assert resp.status_code == 409

    def test_missing_script_json_returns_422(self, client, session):
        _make_campaign(session, script_json=None)
        resp = client.post("/video/generate", json={"campaign_id": "cmp_test"})
        assert resp.status_code == 422
        assert "script_json" in resp.json()["detail"]

    def test_empty_script_json_returns_422(self, client, session):
        _make_campaign(session, script_json="")
        resp = client.post("/video/generate", json={"campaign_id": "cmp_test"})
        assert resp.status_code == 422

    def test_campaign_status_set_to_generating(self, client, session):
        _make_campaign(session)
        with patch("app.api.video._generation_background_task", _noop_bg_task):
            client.post("/video/generate", json={"campaign_id": "cmp_test"})
        session.expire_all()
        from sqlmodel import select
        campaign = session.exec(
            select(Campaign).where(Campaign.campaign_id == "cmp_test")
        ).first()
        assert campaign.status == CampaignStatus.generating

    def test_video_asset_created_with_queued_status(self, client, session):
        _make_campaign(session)
        with patch("app.api.video._generation_background_task", _noop_bg_task):
            client.post("/video/generate", json={"campaign_id": "cmp_test"})
        session.expire_all()
        from sqlmodel import select
        asset = session.exec(
            select(VideoAsset).where(VideoAsset.campaign_id == "cmp_test")
        ).first()
        assert asset is not None
        assert asset.status == "queued"

    def test_existing_video_asset_reset_on_retry(self, client, session):
        """Re-submitting generation resets a prior VideoAsset to queued."""
        _make_campaign(session)
        _make_video_asset(
            session, "cmp_test", status="failed",
            video_url="/storage/cmp_test/video.mp4",
        )
        with patch("app.api.video._generation_background_task", _noop_bg_task):
            resp = client.post("/video/generate", json={"campaign_id": "cmp_test"})
        assert resp.status_code == 200
        session.expire_all()
        from sqlmodel import select
        asset = session.exec(
            select(VideoAsset).where(VideoAsset.campaign_id == "cmp_test")
        ).first()
        assert asset.status == "queued"
        assert asset.video_url is None

    def test_background_task_called_with_pipeline_fn(self, client, session):
        """_generation_background_task is scheduled with the current _pipeline_fn."""
        _make_campaign(session)
        captured: list[dict] = []

        def spy_bg_task(**kwargs: Any) -> None:
            captured.append(kwargs)

        with patch("app.api.video._generation_background_task", spy_bg_task):
            client.post("/video/generate", json={"campaign_id": "cmp_test"})

        assert len(captured) == 1
        assert captured[0]["campaign_id"] == "cmp_test"
        assert callable(captured[0]["pipeline_fn"])

    def test_request_body_missing_campaign_id_returns_422(self, client):
        resp = client.post("/video/generate", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# TestStatusEndpoint
# ---------------------------------------------------------------------------


class TestStatusEndpoint:
    """GET /video/status/{task_id}"""

    def test_unknown_task_id_returns_404(self, client):
        resp = client.get("/video/status/no_such_task")
        assert resp.status_code == 404

    def test_status_by_campaign_id_queued(self, client, session):
        _make_video_asset(session, "cmp_status", status="queued")
        resp = client.get("/video/status/cmp_status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["campaign_id"] == "cmp_status"
        assert body["status"] == "queued"

    def test_status_by_campaign_id_ready_includes_urls(self, client, session):
        _make_video_asset(
            session, "cmp_done",
            status="ready",
            video_url="/storage/cmp_done/video.mp4",
            poster_url="/storage/cmp_done/poster.jpg",
        )
        resp = client.get("/video/status/cmp_done")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ready"
        assert body["video_url"] == "/storage/cmp_done/video.mp4"
        assert body["poster_url"] == "/storage/cmp_done/poster.jpg"

    def test_status_by_campaign_id_omits_urls_when_not_ready(self, client, session):
        _make_video_asset(session, "cmp_queued", status="queued")
        resp = client.get("/video/status/cmp_queued")
        body = resp.json()
        assert "video_url" not in body
        assert "poster_url" not in body

    def test_status_by_runway_task_id(self, client, session):
        _make_runway_task(session, "rt-abc-123", "cmp_test", kind="image_to_video")
        resp = client.get("/video/status/rt-abc-123")
        assert resp.status_code == 200
        body = resp.json()
        assert body["task_id"] == "rt-abc-123"
        assert body["kind"] == "image_to_video"
        assert body["status"] == "succeeded"
        assert body["campaign_id"] == "cmp_test"
        assert body["output_url"] == "https://runway.example.com/clip.mp4"

    def test_status_by_campaign_id_includes_sub_task_ids(self, client, session):
        _make_video_asset(session, "cmp_multi", status="ready")
        _make_runway_task(session, "rt-img-1", "cmp_multi", kind="text_to_image")
        _make_runway_task(session, "rt-vid-1", "cmp_multi", kind="image_to_video")
        _make_runway_task(session, "rt-tts-1", "cmp_multi", kind="tts")
        resp = client.get("/video/status/cmp_multi")
        body = resp.json()
        assert set(body["runway_task_ids"]) == {"rt-img-1", "rt-vid-1", "rt-tts-1"}

    def test_runway_task_id_takes_priority_over_campaign_id(self, client, session):
        """If a task_id matches both RunwayTask.task_id and VideoAsset.campaign_id,
        the RunwayTask row is returned (it is checked first)."""
        _make_runway_task(session, "shared-id", "cmp_x", kind="tts", status="running")
        _make_video_asset(session, "shared-id", status="queued")
        resp = client.get("/video/status/shared-id")
        body = resp.json()
        # RunwayTask has "task_id" key; VideoAsset response doesn't
        assert "task_id" in body
        assert body["kind"] == "tts"
        assert body["status"] == "running"


# ---------------------------------------------------------------------------
# TestPipelineHelpers
# ---------------------------------------------------------------------------


class TestPipelineHelpers:
    """Unit tests for _apply_pipeline_result and _apply_pipeline_failure.

    These helpers take an open session so they can be exercised directly
    with the in-memory test DB, bypassing the BackgroundTask DB isolation.
    """

    from app.api.video import _apply_pipeline_failure, _apply_pipeline_result

    def test_apply_result_sets_video_asset_ready(self, session):
        from app.api.video import _apply_pipeline_result

        campaign = _make_campaign(session, status=CampaignStatus.generating)
        _make_video_asset(session, "cmp_test", status="generating")
        result = PipelineResult(
            campaign_id="cmp_test",
            video_path="/storage/cmp_test/video.mp4",
            poster_path="/storage/cmp_test/poster.jpg",
            voiceover_path="/storage/cmp_test/voiceover.mp3",
        )
        _apply_pipeline_result(session, campaign, result)

        session.expire_all()
        from sqlmodel import select
        asset = session.exec(
            select(VideoAsset).where(VideoAsset.campaign_id == "cmp_test")
        ).first()
        assert asset.status == "ready"
        assert asset.video_url == "/storage/cmp_test/video.mp4"
        assert asset.poster_url == "/storage/cmp_test/poster.jpg"

    def test_apply_result_sets_campaign_ready(self, session):
        from app.api.video import _apply_pipeline_result

        campaign = _make_campaign(session, status=CampaignStatus.generating)
        _make_video_asset(session, "cmp_test")
        result = PipelineResult(
            campaign_id="cmp_test",
            video_path="/v.mp4",
            poster_path="/p.jpg",
            voiceover_path="",
        )
        _apply_pipeline_result(session, campaign, result)

        session.expire_all()
        from sqlmodel import select
        c = session.exec(
            select(Campaign).where(Campaign.campaign_id == "cmp_test")
        ).first()
        assert c.status == CampaignStatus.ready

    def test_apply_failure_sets_video_asset_failed(self, session):
        from app.api.video import _apply_pipeline_failure

        campaign = _make_campaign(session, status=CampaignStatus.generating)
        _make_video_asset(session, "cmp_test", status="generating")
        _apply_pipeline_failure(session, campaign)

        session.expire_all()
        from sqlmodel import select
        asset = session.exec(
            select(VideoAsset).where(VideoAsset.campaign_id == "cmp_test")
        ).first()
        assert asset.status == "failed"

    def test_apply_failure_sets_campaign_generation_failed(self, session):
        from app.api.video import _apply_pipeline_failure

        campaign = _make_campaign(session, status=CampaignStatus.generating)
        _make_video_asset(session, "cmp_test")
        _apply_pipeline_failure(session, campaign)

        session.expire_all()
        from sqlmodel import select
        c = session.exec(
            select(Campaign).where(Campaign.campaign_id == "cmp_test")
        ).first()
        assert c.status == CampaignStatus.generation_failed

    def test_apply_failure_without_video_asset_does_not_raise(self, session):
        """If VideoAsset doesn't exist yet, _apply_pipeline_failure is safe."""
        from app.api.video import _apply_pipeline_failure

        campaign = _make_campaign(session, status=CampaignStatus.generating)
        # No VideoAsset row — should not raise.
        _apply_pipeline_failure(session, campaign)

        session.expire_all()
        from sqlmodel import select
        c = session.exec(
            select(Campaign).where(Campaign.campaign_id == "cmp_test")
        ).first()
        assert c.status == CampaignStatus.generation_failed

    def test_apply_result_creates_video_asset_if_missing(self, session):
        """_apply_pipeline_result creates VideoAsset if it wasn't pre-created."""
        from app.api.video import _apply_pipeline_result

        campaign = _make_campaign(session, status=CampaignStatus.generating)
        # No VideoAsset row.
        result = PipelineResult(
            campaign_id="cmp_test",
            video_path="/v.mp4",
            poster_path="/p.jpg",
            voiceover_path="",
        )
        _apply_pipeline_result(session, campaign, result)

        session.expire_all()
        from sqlmodel import select
        asset = session.exec(
            select(VideoAsset).where(VideoAsset.campaign_id == "cmp_test")
        ).first()
        assert asset is not None
        assert asset.status == "ready"

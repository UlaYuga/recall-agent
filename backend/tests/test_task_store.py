"""Tests for app.runway.task_store.

All tests use an isolated in-memory SQLite session; no real DB is touched.
"""
from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401 — registers RunwayTask (and all tables) in metadata
from app.runway.task_store import create_task, get_task, list_tasks, update_task


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    engine.dispose()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make(session, *, task_id="t-001", campaign_id="cmp-001", kind="image_to_video", **kw):
    return create_task(
        session,
        task_id=task_id,
        campaign_id=campaign_id,
        kind=kind,
        **kw,
    )


# ---------------------------------------------------------------------------
# create_task
# ---------------------------------------------------------------------------


def test_create_task_persists(session):
    task = _make(session, task_id="t-001", campaign_id="cmp-001", kind="image_to_video")
    assert task.id is not None
    assert task.task_id == "t-001"
    assert task.campaign_id == "cmp-001"
    assert task.kind == "image_to_video"


def test_create_task_default_status_pending(session):
    task = _make(session)
    assert task.status == "pending"


def test_create_task_default_retry_count_zero(session):
    task = _make(session)
    assert task.retry_count == 0


def test_create_task_sets_created_at(session):
    task = _make(session)
    assert task.created_at is not None


def test_create_task_updated_at_none_initially(session):
    task = _make(session)
    assert task.updated_at is None


def test_create_task_with_all_optional_fields(session):
    task = create_task(
        session,
        task_id="t-full",
        campaign_id="cmp-full",
        kind="text_to_image",
        model="gen4_image_turbo",
        scene_id="scene-1",
        credits_estimated=2,
        status="running",
    )
    assert task.model == "gen4_image_turbo"
    assert task.scene_id == "scene-1"
    assert task.credits_estimated == 2
    assert task.status == "running"


def test_create_task_tts_kind(session):
    task = _make(session, task_id="tts-001", kind="tts", model="eleven_multilingual_v2")
    assert task.kind == "tts"
    assert task.model == "eleven_multilingual_v2"


def test_create_two_tasks_different_ids(session):
    t1 = _make(session, task_id="t-001", campaign_id="cmp-001")
    t2 = _make(session, task_id="t-002", campaign_id="cmp-001")
    assert t1.id != t2.id


# ---------------------------------------------------------------------------
# get_task
# ---------------------------------------------------------------------------


def test_get_task_returns_correct_row(session):
    _make(session, task_id="t-001")
    _make(session, task_id="t-002")
    found = get_task(session, "t-001")
    assert found is not None
    assert found.task_id == "t-001"


def test_get_task_returns_none_when_missing(session):
    assert get_task(session, "nonexistent") is None


def test_get_task_does_not_return_other_tasks(session):
    _make(session, task_id="t-001", campaign_id="cmp-A")
    found = get_task(session, "t-999")
    assert found is None


# ---------------------------------------------------------------------------
# list_tasks
# ---------------------------------------------------------------------------


def test_list_tasks_returns_all_for_campaign(session):
    _make(session, task_id="t-001", campaign_id="cmp-001", kind="image_to_video")
    _make(session, task_id="t-002", campaign_id="cmp-001", kind="tts")
    _make(session, task_id="t-003", campaign_id="cmp-001", kind="text_to_image")
    tasks = list_tasks(session, "cmp-001")
    assert len(tasks) == 3


def test_list_tasks_empty_for_unknown_campaign(session):
    _make(session, task_id="t-001", campaign_id="cmp-001")
    tasks = list_tasks(session, "cmp-999")
    assert tasks == []


def test_list_tasks_isolates_campaigns(session):
    _make(session, task_id="t-001", campaign_id="cmp-A")
    _make(session, task_id="t-002", campaign_id="cmp-B")
    assert len(list_tasks(session, "cmp-A")) == 1
    assert len(list_tasks(session, "cmp-B")) == 1


def test_list_tasks_filter_by_kind(session):
    _make(session, task_id="t-001", campaign_id="cmp-001", kind="image_to_video")
    _make(session, task_id="t-002", campaign_id="cmp-001", kind="image_to_video")
    _make(session, task_id="t-003", campaign_id="cmp-001", kind="tts")
    iv_tasks = list_tasks(session, "cmp-001", kind="image_to_video")
    tts_tasks = list_tasks(session, "cmp-001", kind="tts")
    assert len(iv_tasks) == 2
    assert len(tts_tasks) == 1


def test_list_tasks_filter_kind_returns_empty_when_none_match(session):
    _make(session, task_id="t-001", campaign_id="cmp-001", kind="image_to_video")
    tasks = list_tasks(session, "cmp-001", kind="tts")
    assert tasks == []


def test_list_tasks_returns_list_type(session):
    result = list_tasks(session, "cmp-001")
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# update_task
# ---------------------------------------------------------------------------


def test_update_task_status(session):
    _make(session, task_id="t-001")
    updated = update_task(session, "t-001", status="succeeded")
    assert updated is not None
    assert updated.status == "succeeded"


def test_update_task_output_url(session):
    _make(session, task_id="t-001")
    updated = update_task(session, "t-001", output_url="https://cdn.example.com/out.mp4")
    assert updated.output_url == "https://cdn.example.com/out.mp4"


def test_update_task_failure_code(session):
    _make(session, task_id="t-001")
    updated = update_task(session, "t-001", status="failed", failure_code="SAFETY.INPUT.TEXT")
    assert updated.status == "failed"
    assert updated.failure_code == "SAFETY.INPUT.TEXT"


def test_update_task_retry_count(session):
    _make(session, task_id="t-001")
    updated = update_task(session, "t-001", retry_count=2)
    assert updated.retry_count == 2


def test_update_task_sets_updated_at(session):
    _make(session, task_id="t-001")
    updated = update_task(session, "t-001", status="running")
    assert updated.updated_at is not None


def test_update_task_returns_none_for_missing_id(session):
    result = update_task(session, "nonexistent", status="succeeded")
    assert result is None


def test_update_task_partial_leaves_other_fields(session):
    _make(session, task_id="t-001", kind="tts", model="eleven_multilingual_v2")
    updated = update_task(session, "t-001", status="running")
    # Fields not passed should be unchanged
    assert updated.kind == "tts"
    assert updated.model == "eleven_multilingual_v2"
    assert updated.retry_count == 0


def test_update_task_multiple_fields_at_once(session):
    _make(session, task_id="t-001")
    updated = update_task(
        session,
        "t-001",
        status="succeeded",
        output_url="https://runway.example.com/v.mp4",
        retry_count=1,
    )
    assert updated.status == "succeeded"
    assert updated.output_url == "https://runway.example.com/v.mp4"
    assert updated.retry_count == 1


def test_update_task_is_readable_via_get(session):
    _make(session, task_id="t-001")
    update_task(session, "t-001", status="succeeded", output_url="https://cdn.example.com/v.mp4")
    fetched = get_task(session, "t-001")
    assert fetched.status == "succeeded"
    assert fetched.output_url == "https://cdn.example.com/v.mp4"


def test_update_does_not_affect_other_tasks(session):
    _make(session, task_id="t-001")
    _make(session, task_id="t-002")
    update_task(session, "t-001", status="succeeded")
    t2 = get_task(session, "t-002")
    assert t2.status == "pending"


# ---------------------------------------------------------------------------
# Full lifecycle
# ---------------------------------------------------------------------------


def test_full_lifecycle_create_update_get(session):
    # Create → running → succeeded with output
    create_task(
        session,
        task_id="t-life",
        campaign_id="cmp-001",
        kind="image_to_video",
        model="gen4.5",
        scene_id="scene-2",
        credits_estimated=120,
    )

    update_task(session, "t-life", status="running")
    mid = get_task(session, "t-life")
    assert mid.status == "running"

    update_task(
        session,
        "t-life",
        status="succeeded",
        output_url="https://cdn.example.com/scene2.mp4",
    )
    final = get_task(session, "t-life")
    assert final.status == "succeeded"
    assert final.credits_estimated == 120
    assert final.output_url == "https://cdn.example.com/scene2.mp4"
    assert final.updated_at is not None


def test_campaign_with_mixed_kinds(session):
    # Typical campaign: 4 image_to_video scenes + 1 tts + 4 text_to_image frames
    for i in range(4):
        create_task(
            session,
            task_id=f"i2v-{i}",
            campaign_id="cmp-mix",
            kind="image_to_video",
            model="gen4.5",
            credits_estimated=120,
        )
    create_task(
        session, task_id="tts-0", campaign_id="cmp-mix", kind="tts", credits_estimated=11
    )
    for i in range(4):
        create_task(
            session,
            task_id=f"t2i-{i}",
            campaign_id="cmp-mix",
            kind="text_to_image",
            model="gen4_image_turbo",
            credits_estimated=2,
        )

    all_tasks = list_tasks(session, "cmp-mix")
    assert len(all_tasks) == 9
    assert len(list_tasks(session, "cmp-mix", kind="image_to_video")) == 4
    assert len(list_tasks(session, "cmp-mix", kind="tts")) == 1
    assert len(list_tasks(session, "cmp-mix", kind="text_to_image")) == 4

    total_credits = sum(t.credits_estimated or 0 for t in all_tasks)
    assert total_credits == 4 * 120 + 11 + 4 * 2  # 480 + 11 + 8 = 499

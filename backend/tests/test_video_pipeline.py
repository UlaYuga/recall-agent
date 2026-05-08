"""Tests for app.runway.video_pipeline.

All RunwayClient calls are mocked.
The stitch boundary is replaced with a lightweight stub.
A real in-memory SQLite session is used so task_store assertions work.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401 — registers all SQLModel tables in metadata
from app.models import Campaign
from app.runway.client import RunwayTaskError
from app.runway.credit_estimator import estimate_image, estimate_tts, estimate_video
from app.runway.schemas import RunwayTask
from app.runway.task_store import list_tasks
from app.runway.video_pipeline import PipelineResult, run_video_pipeline


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    engine.dispose()


def _make_campaign(
    n_scenes: int = 2,
    with_voiceover: bool = True,
    game_label: str | None = None,
    game_category: str | None = None,
) -> Campaign:
    scenes = [
        {
            "id": i,
            "type": "scene",
            "text": f"Scene {i} text.",
            "visual_brief": "abstract motion, cinematic dark backdrop, no text, no logos",
        }
        for i in range(1, n_scenes + 1)
    ]
    script: dict = {"scenes": scenes}
    if with_voiceover:
        script["full_voiceover_text"] = "Welcome back. Your bonus is ready."
    if game_label:
        script["game_label"] = game_label
    if game_category:
        script["game_category"] = game_category
    return Campaign(
        campaign_id="cmp_test",
        player_id="p_001",
        script_json=json.dumps(script),
    )


def _make_client(n_scenes: int = 2, fail_task_id: str | None = None) -> MagicMock:
    """Build a MagicMock RunwayClient with deterministic per-call task IDs."""
    client = MagicMock()

    client.create_text_to_image.side_effect = [
        f"img-task-{i:03d}" for i in range(1, n_scenes + 1)
    ]
    client.create_image_to_video.side_effect = [
        f"vid-task-{i:03d}" for i in range(1, n_scenes + 1)
    ]
    client.create_tts.return_value = "tts-task-001"

    def _get_task(task_id: str) -> RunwayTask:
        if task_id == fail_task_id:
            return RunwayTask(
                id=task_id,
                status="FAILED",
                failure="Internal error",
                failure_code="INTERNAL",
            )
        return RunwayTask(id=task_id, status="SUCCEEDED", output=["https://example.com/out"])

    client.get_task.side_effect = _get_task
    client.download_output.return_value = b"fake-bytes"
    return client


def _mock_stitch(
    clip_paths: list[str], voiceover_path: str | None, output_dir: Path
) -> tuple[str, str]:
    """Lightweight stitch stub that writes placeholder files."""
    mp4 = output_dir / "video.mp4"
    poster = output_dir / "poster.jpg"
    output_dir.mkdir(parents=True, exist_ok=True)
    mp4.write_bytes(b"fake-mp4")
    poster.write_bytes(b"fake-jpg")
    return str(mp4.resolve()), str(poster.resolve())


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_returns_pipeline_result(self, db_session, tmp_path):
        with patch("app.runway.video_pipeline.time.sleep"):
            result = run_video_pipeline(
                _make_campaign(),
                client=_make_client(),
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        assert isinstance(result, PipelineResult)
        assert result.campaign_id == "cmp_test"

    def test_clip_paths_written_to_storage(self, db_session, tmp_path):
        with patch("app.runway.video_pipeline.time.sleep"):
            result = run_video_pipeline(
                _make_campaign(n_scenes=2),
                client=_make_client(n_scenes=2),
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        assert len(result.clip_paths) == 2
        for p in result.clip_paths:
            assert Path(p).exists()
            assert Path(p).read_bytes() == b"fake-bytes"

    def test_start_frames_written_to_storage(self, db_session, tmp_path):
        with patch("app.runway.video_pipeline.time.sleep"):
            run_video_pipeline(
                _make_campaign(n_scenes=2),
                client=_make_client(n_scenes=2),
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        frames = list((tmp_path / "cmp_test").glob("scene_*_frame.jpg"))
        assert len(frames) == 2

    def test_voiceover_written_to_storage(self, db_session, tmp_path):
        with patch("app.runway.video_pipeline.time.sleep"):
            result = run_video_pipeline(
                _make_campaign(with_voiceover=True),
                client=_make_client(),
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        assert result.voiceover_path
        assert Path(result.voiceover_path).exists()

    def test_mp4_and_poster_paths_from_stitch(self, db_session, tmp_path):
        with patch("app.runway.video_pipeline.time.sleep"):
            result = run_video_pipeline(
                _make_campaign(),
                client=_make_client(),
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        assert Path(result.video_path).name == "video.mp4"
        assert Path(result.poster_path).name == "poster.jpg"
        assert Path(result.video_path).exists()
        assert Path(result.poster_path).exists()

    def test_result_paths_are_absolute(self, db_session, tmp_path):
        with patch("app.runway.video_pipeline.time.sleep"):
            result = run_video_pipeline(
                _make_campaign(),
                client=_make_client(),
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        assert Path(result.video_path).is_absolute()
        assert Path(result.poster_path).is_absolute()
        for p in result.clip_paths:
            assert Path(p).is_absolute()


# ---------------------------------------------------------------------------
# Client call assertions
# ---------------------------------------------------------------------------


class TestClientCalls:
    def test_create_text_to_image_called_per_scene(self, db_session, tmp_path):
        client = _make_client(n_scenes=3)
        with patch("app.runway.video_pipeline.time.sleep"):
            run_video_pipeline(
                _make_campaign(n_scenes=3),
                client=client,
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        assert client.create_text_to_image.call_count == 3

    def test_create_image_to_video_called_per_scene(self, db_session, tmp_path):
        client = _make_client(n_scenes=3)
        with patch("app.runway.video_pipeline.time.sleep"):
            run_video_pipeline(
                _make_campaign(n_scenes=3),
                client=client,
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        assert client.create_image_to_video.call_count == 3

    def test_create_tts_called_once_with_voiceover(self, db_session, tmp_path):
        client = _make_client()
        with patch("app.runway.video_pipeline.time.sleep"):
            run_video_pipeline(
                _make_campaign(with_voiceover=True),
                client=client,
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        client.create_tts.assert_called_once()
        req = client.create_tts.call_args.args[0]
        assert req.prompt_text == "Welcome back. Your bonus is ready."

    def test_create_tts_not_called_without_voiceover(self, db_session, tmp_path):
        client = _make_client()
        with patch("app.runway.video_pipeline.time.sleep"):
            run_video_pipeline(
                _make_campaign(with_voiceover=False),
                client=client,
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        client.create_tts.assert_not_called()

    def test_image_to_video_uses_data_uri(self, db_session, tmp_path):
        client = _make_client()
        with patch("app.runway.video_pipeline.time.sleep"):
            run_video_pipeline(
                _make_campaign(n_scenes=1),
                client=client,
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        req = client.create_image_to_video.call_args.args[0]
        assert req.prompt_image.startswith("data:image/jpeg;base64,")

    def test_safe_prompt_passed_to_image_generation(self, db_session, tmp_path):
        client = _make_client()
        with patch("app.runway.video_pipeline.time.sleep"):
            run_video_pipeline(
                _make_campaign(n_scenes=1),
                client=client,
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        req = client.create_text_to_image.call_args.args[0]
        assert "no text" in req.prompt_text
        assert "no logos" in req.prompt_text

    def test_stitch_fn_called_with_clip_paths_and_voiceover(self, db_session, tmp_path):
        stitch_calls: list[tuple] = []

        def capturing_stitch(clips, vo, out_dir):
            stitch_calls.append((clips, vo, out_dir))
            return _mock_stitch(clips, vo, out_dir)

        client = _make_client(n_scenes=2)
        with patch("app.runway.video_pipeline.time.sleep"):
            run_video_pipeline(
                _make_campaign(n_scenes=2, with_voiceover=True),
                client=client,
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=capturing_stitch,
            )

        assert len(stitch_calls) == 1
        clips, vo, _ = stitch_calls[0]
        assert len(clips) == 2
        assert vo is not None
        assert vo.endswith("voiceover.mp3")

    def test_stitch_fn_receives_none_voiceover_when_no_tts(self, db_session, tmp_path):
        stitch_calls: list[tuple] = []

        def capturing_stitch(clips, vo, out_dir):
            stitch_calls.append((clips, vo, out_dir))
            return _mock_stitch(clips, vo, out_dir)

        with patch("app.runway.video_pipeline.time.sleep"):
            run_video_pipeline(
                _make_campaign(with_voiceover=False),
                client=_make_client(),
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=capturing_stitch,
            )

        _, vo, _ = stitch_calls[0]
        assert vo is None


# ---------------------------------------------------------------------------
# Credit estimation
# ---------------------------------------------------------------------------


class TestCreditEstimation:
    def test_credits_estimated_correctly(self, db_session, tmp_path):
        n = 2
        voiceover = "Welcome back. Your bonus is ready."
        expected = (
            n * estimate_image("gen4_image_turbo")
            + n * estimate_video("gen4.5", 10)
            + estimate_tts(voiceover)
        )
        with patch("app.runway.video_pipeline.time.sleep"):
            result = run_video_pipeline(
                _make_campaign(n_scenes=n, with_voiceover=True),
                client=_make_client(n_scenes=n),
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        assert result.credits_estimated == expected

    def test_no_tts_credits_without_voiceover(self, db_session, tmp_path):
        n = 2
        expected_no_tts = (
            n * estimate_image("gen4_image_turbo") + n * estimate_video("gen4.5", 10)
        )
        with patch("app.runway.video_pipeline.time.sleep"):
            result = run_video_pipeline(
                _make_campaign(n_scenes=n, with_voiceover=False),
                client=_make_client(n_scenes=n),
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        assert result.credits_estimated == expected_no_tts


# ---------------------------------------------------------------------------
# Task store persistence
# ---------------------------------------------------------------------------


class TestTaskStorePersistence:
    def test_text_to_image_tasks_persisted(self, db_session, tmp_path):
        with patch("app.runway.video_pipeline.time.sleep"):
            run_video_pipeline(
                _make_campaign(n_scenes=2),
                client=_make_client(n_scenes=2),
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        img_tasks = list_tasks(db_session, "cmp_test", kind="text_to_image")
        assert len(img_tasks) == 2
        for t in img_tasks:
            assert t.model == "gen4_image_turbo"
            assert t.credits_estimated == estimate_image("gen4_image_turbo")

    def test_image_to_video_tasks_persisted(self, db_session, tmp_path):
        with patch("app.runway.video_pipeline.time.sleep"):
            run_video_pipeline(
                _make_campaign(n_scenes=2),
                client=_make_client(n_scenes=2),
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        vid_tasks = list_tasks(db_session, "cmp_test", kind="image_to_video")
        assert len(vid_tasks) == 2
        for t in vid_tasks:
            assert t.model == "gen4.5"
            assert t.credits_estimated == estimate_video("gen4.5", 10)

    def test_tts_task_persisted(self, db_session, tmp_path):
        with patch("app.runway.video_pipeline.time.sleep"):
            run_video_pipeline(
                _make_campaign(with_voiceover=True),
                client=_make_client(),
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        tts_tasks = list_tasks(db_session, "cmp_test", kind="tts")
        assert len(tts_tasks) == 1
        assert tts_tasks[0].model == "eleven_multilingual_v2"

    def test_succeeded_tasks_have_output_url(self, db_session, tmp_path):
        with patch("app.runway.video_pipeline.time.sleep"):
            run_video_pipeline(
                _make_campaign(n_scenes=1),
                client=_make_client(n_scenes=1),
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        all_tasks = list_tasks(db_session, "cmp_test")
        for t in all_tasks:
            assert t.output_url == "https://example.com/out"

    def test_all_task_ids_in_result(self, db_session, tmp_path):
        with patch("app.runway.video_pipeline.time.sleep"):
            result = run_video_pipeline(
                _make_campaign(n_scenes=2, with_voiceover=True),
                client=_make_client(n_scenes=2),
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        # 2 scenes × (1 img + 1 vid) + 1 tts = 5 task IDs
        assert len(result.runway_task_ids) == 5

    def test_scene_id_stored_on_tasks(self, db_session, tmp_path):
        with patch("app.runway.video_pipeline.time.sleep"):
            run_video_pipeline(
                _make_campaign(n_scenes=2),
                client=_make_client(n_scenes=2),
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        img_tasks = list_tasks(db_session, "cmp_test", kind="text_to_image")
        scene_ids = {t.scene_id for t in img_tasks}
        assert scene_ids == {"1", "2"}


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------


class TestErrorPropagation:
    def test_failed_image_task_raises(self, db_session, tmp_path):
        client = _make_client(n_scenes=1, fail_task_id="img-task-001")
        with patch("app.runway.video_pipeline.time.sleep"):
            with pytest.raises(RunwayTaskError, match="FAILED"):
                run_video_pipeline(
                    _make_campaign(n_scenes=1),
                    client=client,
                    session=db_session,
                    storage_dir=tmp_path,
                    stitch_fn=_mock_stitch,
                )

    def test_failed_video_task_raises(self, db_session, tmp_path):
        client = _make_client(n_scenes=1, fail_task_id="vid-task-001")
        with patch("app.runway.video_pipeline.time.sleep"):
            with pytest.raises(RunwayTaskError, match="FAILED"):
                run_video_pipeline(
                    _make_campaign(n_scenes=1),
                    client=client,
                    session=db_session,
                    storage_dir=tmp_path,
                    stitch_fn=_mock_stitch,
                )

    def test_failed_tts_task_raises(self, db_session, tmp_path):
        client = _make_client(n_scenes=1, fail_task_id="tts-task-001")
        with patch("app.runway.video_pipeline.time.sleep"):
            with pytest.raises(RunwayTaskError, match="FAILED"):
                run_video_pipeline(
                    _make_campaign(n_scenes=1, with_voiceover=True),
                    client=client,
                    session=db_session,
                    storage_dir=tmp_path,
                    stitch_fn=_mock_stitch,
                )

    def test_failed_task_updates_status_in_store(self, db_session, tmp_path):
        client = _make_client(n_scenes=1, fail_task_id="img-task-001")
        with patch("app.runway.video_pipeline.time.sleep"):
            with pytest.raises(RunwayTaskError):
                run_video_pipeline(
                    _make_campaign(n_scenes=1),
                    client=client,
                    session=db_session,
                    storage_dir=tmp_path,
                    stitch_fn=_mock_stitch,
                )
        img_tasks = list_tasks(db_session, "cmp_test", kind="text_to_image")
        assert img_tasks[0].status == "failed"
        assert img_tasks[0].failure_code == "INTERNAL"


# ---------------------------------------------------------------------------
# Game label / visual mode
# ---------------------------------------------------------------------------


class TestVisualPrompt:
    def test_game_label_triggers_b04_hint(self, db_session, tmp_path):
        client = _make_client(n_scenes=1)
        with patch("app.runway.video_pipeline.time.sleep"):
            run_video_pipeline(
                _make_campaign(n_scenes=1, game_label="neon_spins"),
                client=client,
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        req = client.create_text_to_image.call_args.args[0]
        # B-04 neon_spins hint contains "neon" or "electric"
        assert "neon" in req.prompt_text.lower() or "electric" in req.prompt_text.lower()

    def test_prompt_always_contains_safety_markers(self, db_session, tmp_path):
        client = _make_client(n_scenes=2)
        with patch("app.runway.video_pipeline.time.sleep"):
            run_video_pipeline(
                _make_campaign(n_scenes=2),
                client=client,
                session=db_session,
                storage_dir=tmp_path,
                stitch_fn=_mock_stitch,
            )
        for call in client.create_text_to_image.call_args_list:
            prompt = call.args[0].prompt_text
            assert "no text" in prompt
            assert "no logos" in prompt

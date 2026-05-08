"""Runway video generation pipeline: approved Campaign → mp4 + poster.

Flow per campaign
-----------------
1. Parse scenes from campaign.script_json.
2. For every scene: generate start frame (text_to_image) → scene clip (image_to_video).
3. Generate voiceover via TTS.
4. Stitch clips + audio into final mp4 and extract poster.
5. Return PipelineResult with all paths and audit metadata.

No API routes. No delivery adapters. No dashboard code.
All RunwayClient and stitch calls are injectable for testing.
"""
from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal

from sqlmodel import Session

from app.models import Campaign
from app.runway.client import RunwayClient, RunwayTaskError
from app.runway.credit_estimator import estimate_image, estimate_tts, estimate_video
from app.runway.prompt_safety import build_safe_visual_prompt, sanitize_visual_brief
from app.runway.schemas import ImageToVideoRequest, RunwayTask, TextToImageRequest, TTSRequest
from app.runway.task_store import create_task, update_task

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

StitchFn = Callable[
    [list[str], "str | None", Path],
    "tuple[str, str]",
]
"""
Concat clips + overlay voiceover, return (mp4_path, poster_path).

Args
----
clip_paths:     Ordered list of local scene mp4 paths.
voiceover_path: Local mp3 path, or None to skip audio overlay.
output_dir:     Directory where final video and poster are written.

Returns absolute paths to the stitched mp4 and the poster jpg.
"""

# Backoff ladder (seconds) matching the Runway retry policy.
_POLL_BACKOFF: list[int] = [15, 45, 120]
_DEFAULT_TIMEOUT_SEC: int = 600

DEFAULT_VIDEO_MODEL: str = "gen4.5"
DEFAULT_IMAGE_MODEL: str = "gen4_image_turbo"
DEFAULT_CLIP_DURATION: Literal[5, 10] = 10
_RATIO: str = "1280:720"


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass
class PipelineResult:
    """All artefacts produced by a completed video generation run."""

    campaign_id: str
    video_path: str            # absolute path to the stitched mp4
    poster_path: str           # absolute path to the poster jpg
    voiceover_path: str        # absolute path to the mp3 (empty when no voiceover)
    clip_paths: list[str] = field(default_factory=list)
    credits_estimated: int = 0
    runway_task_ids: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _image_to_data_uri(path: Path) -> str:
    """Base64-encode a local image file as a Runway-compatible data URI."""
    suffix = path.suffix.lower().lstrip(".")
    mime = "image/jpeg" if suffix in ("jpg", "jpeg") else f"image/{suffix}"
    encoded = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{encoded}"


def _save_bytes(data: bytes, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _safe_prompt(
    raw_brief: str,
    game_label: str | None,
    game_category: str | None,
) -> str:
    """Return a prompt-safety-cleared visual brief for one scene."""
    if game_label or game_category:
        return build_safe_visual_prompt(
            game_label=game_label,
            game_category=game_category,
            extra_brief=raw_brief,
        )
    return sanitize_visual_brief(raw_brief)


def _poll_task(
    client: RunwayClient,
    task_id: str,
    kind: str,
    *,
    session: Session,
    timeout_sec: int,
) -> RunwayTask:
    """Poll client.get_task() until terminal; mirror status into task_store.

    Raises RunwayTaskError on FAILED, CANCELLED, or timeout.
    """
    elapsed = 0
    step = 0
    last_status: str = ""

    while elapsed < timeout_sec:
        runway_task = client.get_task(task_id)
        status_lower = runway_task.status.lower()

        if runway_task.status != last_status:
            update_task(session, task_id, status=status_lower)
            last_status = runway_task.status

        if runway_task.status == "SUCCEEDED":
            if runway_task.output:
                update_task(session, task_id, output_url=runway_task.output[0])
            return runway_task

        if runway_task.status in ("FAILED", "CANCELLED"):
            update_task(
                session, task_id,
                status=status_lower,
                failure_code=runway_task.failure_code,
            )
            raise RunwayTaskError(
                f"{kind} task {task_id} ended with {runway_task.status}: {runway_task.failure}",
                failure_code=runway_task.failure_code,
            )

        delay = _POLL_BACKOFF[min(step, len(_POLL_BACKOFF) - 1)]
        time.sleep(delay)
        elapsed += delay
        step += 1

    raise RunwayTaskError(f"{kind} task {task_id} timed out after {timeout_sec}s.")


# ---------------------------------------------------------------------------
# Default stitch (ffmpeg-python; injectable boundary for tests)
# ---------------------------------------------------------------------------


def _default_stitch(
    clip_paths: list[str],
    voiceover_path: str | None,
    output_dir: Path,
) -> tuple[str, str]:
    """Concatenate clips + overlay voiceover via ffmpeg-python.

    Substitute a mock or stub in tests — the real binary is not required there.
    """
    import ffmpeg  # noqa: PLC0415

    output_dir.mkdir(parents=True, exist_ok=True)
    mp4_out = output_dir / "video.mp4"
    poster_out = output_dir / "poster.jpg"

    streams = [ffmpeg.input(p) for p in clip_paths]
    v_streams = [s.video for s in streams]
    a_streams = [s.audio for s in streams]
    interleaved = [x for pair in zip(v_streams, a_streams) for x in pair]
    concat = ffmpeg.concat(*interleaved, v=1, a=1)
    v_out, a_out = concat["v"], concat["a"]

    if voiceover_path:
        vo = ffmpeg.input(voiceover_path).audio
        a_out = ffmpeg.filter([a_out, vo], "amix", inputs=2, duration="first")

    (
        ffmpeg.output(
            v_out, a_out, str(mp4_out),
            vcodec="libx264", acodec="aac",
            pix_fmt="yuv420p", r=24, movflags="+faststart",
        )
        .overwrite_output()
        .run(quiet=True)
    )

    (
        ffmpeg.input(str(mp4_out), ss=0)
        .output(str(poster_out), vframes=1)
        .overwrite_output()
        .run(quiet=True)
    )

    return str(mp4_out.resolve()), str(poster_out.resolve())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_video_pipeline(
    campaign: Campaign,
    *,
    client: RunwayClient,
    session: Session,
    storage_dir: str | Path = "./storage",
    video_model: str = DEFAULT_VIDEO_MODEL,
    image_model: str = DEFAULT_IMAGE_MODEL,
    clip_duration: Literal[5, 10] = DEFAULT_CLIP_DURATION,
    stitch_fn: StitchFn | None = None,
    timeout_sec: int = _DEFAULT_TIMEOUT_SEC,
) -> PipelineResult:
    """Run the Runway video generation pipeline for an approved campaign.

    Parameters
    ----------
    campaign:      Approved Campaign with script_json populated.
    client:        RunwayClient instance (inject a MagicMock in tests).
    session:       Open SQLModel Session for task_store persistence.
    storage_dir:   Root directory for generated media files (gitignored).
    video_model:   Runway model for image-to-video clips.
    image_model:   Runway model for start-frame generation.
    clip_duration: Seconds per clip (5 or 10).
    stitch_fn:     Concat + audio-overlay callable; defaults to ffmpeg impl.
    timeout_sec:   Per-task polling timeout in seconds.

    Returns
    -------
    PipelineResult with absolute paths and aggregate credit + task metadata.

    Raises
    ------
    RunwayTaskError
        If any Runway task fails, is cancelled, or times out.
    """
    if stitch_fn is None:
        stitch_fn = _default_stitch

    out_dir = Path(storage_dir) / campaign.campaign_id
    out_dir.mkdir(parents=True, exist_ok=True)

    script: dict = json.loads(campaign.script_json or "{}")
    scenes: list[dict] = script.get("scenes", [])
    voiceover_text: str = script.get("full_voiceover_text", "")
    game_label: str | None = script.get("game_label")
    game_category: str | None = script.get("game_category")

    total_credits = 0
    runway_task_ids: list[str] = []
    clip_paths: list[str] = []

    # ── Scene loop ──────────────────────────────────────────────────────────
    for scene in scenes:
        scene_id = str(scene.get("id", len(clip_paths) + 1))
        safe_prompt = _safe_prompt(
            scene.get("visual_brief", ""),
            game_label,
            game_category,
        )

        # 1. Start frame (text-to-image).
        img_credits = estimate_image(image_model)
        total_credits += img_credits

        img_task_id = client.create_text_to_image(
            TextToImageRequest(model=image_model, prompt_text=safe_prompt, ratio=_RATIO)
        )
        runway_task_ids.append(img_task_id)
        create_task(
            session,
            task_id=img_task_id,
            campaign_id=campaign.campaign_id,
            kind="text_to_image",
            model=image_model,
            scene_id=scene_id,
            credits_estimated=img_credits,
        )

        img_result = _poll_task(client, img_task_id, "image", session=session, timeout_sec=timeout_sec)
        frame_url = (img_result.output or [""])[0]
        frame_bytes = client.download_output(frame_url)
        frame_path = out_dir / f"scene_{scene_id}_frame.jpg"
        _save_bytes(frame_bytes, frame_path)

        # 2. Scene clip (image-to-video).
        vid_credits = estimate_video(video_model, clip_duration)
        total_credits += vid_credits

        vid_task_id = client.create_image_to_video(
            ImageToVideoRequest(
                model=video_model,
                prompt_image=_image_to_data_uri(frame_path),
                prompt_text=safe_prompt,
                ratio=_RATIO,
                duration=clip_duration,
            )
        )
        runway_task_ids.append(vid_task_id)
        create_task(
            session,
            task_id=vid_task_id,
            campaign_id=campaign.campaign_id,
            kind="image_to_video",
            model=video_model,
            scene_id=scene_id,
            credits_estimated=vid_credits,
        )

        vid_result = _poll_task(client, vid_task_id, "video", session=session, timeout_sec=timeout_sec)
        clip_url = (vid_result.output or [""])[0]
        clip_bytes = client.download_output(clip_url)
        clip_path = out_dir / f"clip_{scene_id}.mp4"
        _save_bytes(clip_bytes, clip_path)
        clip_paths.append(str(clip_path.resolve()))

    # ── TTS ─────────────────────────────────────────────────────────────────
    voiceover_path = ""
    if voiceover_text:
        tts_credits = estimate_tts(voiceover_text)
        total_credits += tts_credits

        tts_task_id = client.create_tts(TTSRequest(prompt_text=voiceover_text))
        runway_task_ids.append(tts_task_id)
        create_task(
            session,
            task_id=tts_task_id,
            campaign_id=campaign.campaign_id,
            kind="tts",
            model="eleven_multilingual_v2",
            credits_estimated=tts_credits,
        )

        tts_result = _poll_task(client, tts_task_id, "TTS", session=session, timeout_sec=timeout_sec)
        tts_url = (tts_result.output or [""])[0]
        audio_bytes = client.download_output(tts_url)
        vo_path = out_dir / "voiceover.mp3"
        _save_bytes(audio_bytes, vo_path)
        voiceover_path = str(vo_path.resolve())

    # ── Stitch ──────────────────────────────────────────────────────────────
    mp4_path, poster_path = stitch_fn(clip_paths, voiceover_path or None, out_dir)

    return PipelineResult(
        campaign_id=campaign.campaign_id,
        video_path=mp4_path,
        poster_path=poster_path,
        voiceover_path=voiceover_path,
        clip_paths=clip_paths,
        credits_estimated=total_credits,
        runway_task_ids=runway_task_ids,
    )

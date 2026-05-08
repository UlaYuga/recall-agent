"""TTS pipeline: text → Runway eleven_multilingual_v2 → local mp3.

English-only for MVP reliability.
No video concat, no image/video generation — TTS boundary only.
"""
from __future__ import annotations

import time
from pathlib import Path

from app.runway.client import RunwayClient, RunwayTaskError
from app.runway.credit_estimator import estimate_tts
from app.runway.schemas import RunwayTask, TTSRequest

# Backoff ladder (seconds) from the Runway retry policy.
# After the last value, the last value repeats until timeout.
_POLL_BACKOFF: list[int] = [15, 45, 120]

# Default poll timeout — Runway TTS is fast, but allow headroom.
_DEFAULT_TIMEOUT_SEC: int = 600

# Runway voice preset used for all MVP voiceovers (English).
DEFAULT_VOICE_PRESET: str = "Maya"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _poll_until_done(
    client: RunwayClient,
    task_id: str,
    *,
    timeout_sec: int = _DEFAULT_TIMEOUT_SEC,
) -> RunwayTask:
    """Poll client.get_task until the task reaches a terminal state.

    Returns the completed RunwayTask on SUCCEEDED.
    Raises RunwayTaskError on FAILED, CANCELLED, or timeout.
    """
    elapsed = 0
    step = 0
    while elapsed < timeout_sec:
        task = client.get_task(task_id)
        if task.status == "SUCCEEDED":
            return task
        if task.status in ("FAILED", "CANCELLED"):
            raise RunwayTaskError(
                f"TTS task {task_id} ended with status {task.status}: {task.failure}",
                failure_code=task.failure_code,
            )
        # PENDING, THROTTLED, RUNNING — keep waiting.
        delay = _POLL_BACKOFF[min(step, len(_POLL_BACKOFF) - 1)]
        time.sleep(delay)
        elapsed += delay
        step += 1
    raise RunwayTaskError(
        f"TTS task {task_id} did not complete within {timeout_sec}s."
    )


def _save_audio(data: bytes, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def synthesize_voiceover(
    text: str,
    campaign_id: str,
    *,
    client: RunwayClient,
    voice_preset_id: str = DEFAULT_VOICE_PRESET,
    storage_dir: str | Path = "./storage",
    timeout_sec: int = _DEFAULT_TIMEOUT_SEC,
) -> str:
    """Submit a TTS request, poll, download and save the mp3 locally.

    Parameters
    ----------
    text:
        English voiceover script (70-110 words for MVP).
    campaign_id:
        Campaign identifier; used to build the output directory path.
    client:
        Injected RunwayClient instance (enables mocking in tests).
    voice_preset_id:
        Runway preset voice name.  Defaults to "Maya" (English, neutral).
    storage_dir:
        Root storage directory; must be gitignored.  Defaults to "./storage".
    timeout_sec:
        Hard timeout for polling; raises RunwayTaskError if exceeded.

    Returns
    -------
    str
        Absolute path to the saved ``voiceover.mp3`` file.

    Raises
    ------
    RunwayTaskError
        If the Runway task fails, is cancelled, or times out.
    RunwayAPIError
        If the Runway SDK raises a network or API error.
    """
    # Pre-flight credit estimate (computed before the request; callers may log it).
    _ = estimate_tts(text)

    # Submit.
    request = TTSRequest(
        prompt_text=text,
        voice_preset_id=voice_preset_id,
    )
    task_id = client.create_tts(request)

    # Poll until terminal state.
    task = _poll_until_done(client, task_id, timeout_sec=timeout_sec)

    # Validate output.
    if not task.output:
        raise RunwayTaskError(f"TTS task {task_id} SUCCEEDED but returned no output URLs.")
    output_url = task.output[0]

    # Download.
    audio_bytes = client.download_output(output_url)

    # Persist.
    out_path = Path(storage_dir) / campaign_id / "voiceover.mp3"
    _save_audio(audio_bytes, out_path)

    return str(out_path.resolve())

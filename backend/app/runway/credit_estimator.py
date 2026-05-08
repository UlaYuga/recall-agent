"""Runway credit estimator for the Recall pipeline.

All estimates are pre-flight only — no Runway SDK calls are made here.

Rates (source: docs/research/RUNWAY_API_CHEATSHEET.md):
    gen4.5               12 credits / sec   (image-to-video / text-to-video)
    gen4_turbo            5 credits / sec
    gen4_image_turbo      2 credits / image
    gen4_image            8 credits / image  (1080p)
    eleven_multilingual_v2  1 credit per 50 chars, rounded up
"""
from __future__ import annotations

import math

from app.runway.prompt_safety import strip_forbidden

# ---------------------------------------------------------------------------
# Published rates
# ---------------------------------------------------------------------------

VIDEO_CREDITS_PER_SEC: dict[str, int] = {
    "gen4.5": 12,
    "gen4_turbo": 5,
}

IMAGE_CREDITS: dict[str, int] = {
    "gen4_image_turbo": 2,
    "gen4_image": 8,
}

TTS_CHARS_PER_CREDIT: int = 50

# gen4.5 / gen4_turbo only support 5 s or 10 s clips.
VALID_VIDEO_DURATIONS: frozenset[int] = frozenset({5, 10})

# ---------------------------------------------------------------------------
# Process-lifetime counter
# ---------------------------------------------------------------------------

_total_estimated: int = 0


def get_total() -> int:
    """Return cumulative estimated credits recorded since the last reset."""
    return _total_estimated


def reset_total() -> None:
    """Reset the process-lifetime counter to zero."""
    global _total_estimated
    _total_estimated = 0


def add_to_total(credits: int) -> None:
    """Increment the running total by *credits*.

    Call this after each estimate to track spend for the demo session.
    """
    global _total_estimated
    _total_estimated += credits


# ---------------------------------------------------------------------------
# Per-operation estimates
# ---------------------------------------------------------------------------


def estimate_video(model: str, duration_sec: int) -> int:
    """Credits for one image-to-video or text-to-video task.

    Raises ValueError for an unknown model or unsupported duration.
    """
    if model not in VIDEO_CREDITS_PER_SEC:
        raise ValueError(
            f"Unknown video model {model!r}. "
            f"Supported: {sorted(VIDEO_CREDITS_PER_SEC)}"
        )
    if duration_sec not in VALID_VIDEO_DURATIONS:
        raise ValueError(
            f"Invalid video duration {duration_sec!r}s. "
            f"Supported: {sorted(VALID_VIDEO_DURATIONS)}"
        )
    return VIDEO_CREDITS_PER_SEC[model] * duration_sec


def estimate_image(model: str = "gen4_image_turbo") -> int:
    """Credits for one text-to-image task.

    Raises ValueError for an unknown model.
    """
    if model not in IMAGE_CREDITS:
        raise ValueError(
            f"Unknown image model {model!r}. "
            f"Supported: {sorted(IMAGE_CREDITS)}"
        )
    return IMAGE_CREDITS[model]


def estimate_tts(prompt_text: str) -> int:
    """Credits for one TTS task (eleven_multilingual_v2).

    Rate: 1 credit per 50 chars, rounded up.
    prompt_text is sanitized via strip_forbidden before the character count is
    measured so forbidden brand / game-title references do not inflate the estimate.
    """
    safe_text = strip_forbidden(prompt_text)
    return math.ceil(len(safe_text) / TTS_CHARS_PER_CREDIT)


# ---------------------------------------------------------------------------
# Aggregate plan estimate
# ---------------------------------------------------------------------------


def estimate_video_plan(
    *,
    scene_count: int,
    video_model: str = "gen4.5",
    duration_sec: int = 10,
    image_model: str = "gen4_image_turbo",
    tts_text: str = "",
    include_images: bool = True,
) -> dict[str, int]:
    """Aggregate credit estimate for a multi-scene video campaign.

    Args:
        scene_count:    Number of video clips to generate.
        video_model:    Model for image-to-video ("gen4.5" or "gen4_turbo").
        duration_sec:   Clip duration in seconds (5 or 10).
        image_model:    Model for start-frame generation.
        tts_text:       Full voiceover text; empty string skips TTS estimate.
        include_images: Whether start frames are generated (default True).

    Returns:
        Breakdown dict::

            {
                "video":  credits for all scene clips,
                "images": credits for all start frames (0 if include_images=False),
                "tts":    credits for voiceover (0 if tts_text is empty),
                "total":  sum of all,
            }
    """
    video_credits = scene_count * estimate_video(video_model, duration_sec)
    image_credits = scene_count * estimate_image(image_model) if include_images else 0
    tts_credits = estimate_tts(tts_text) if tts_text else 0
    total = video_credits + image_credits + tts_credits
    return {
        "video": video_credits,
        "images": image_credits,
        "tts": tts_credits,
        "total": total,
    }

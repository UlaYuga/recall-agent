"""Tests for app.runway.credit_estimator.

Covers: rate math, TTS rounding, aggregate plan totals, counter
reset/increment, invalid model and duration errors, and brand
sanitization before TTS char-count.
"""
from __future__ import annotations

import pytest

from app.runway.credit_estimator import (
    IMAGE_CREDITS,
    TTS_CHARS_PER_CREDIT,
    VIDEO_CREDITS_PER_SEC,
    VALID_VIDEO_DURATIONS,
    add_to_total,
    estimate_image,
    estimate_tts,
    estimate_video,
    estimate_video_plan,
    get_total,
    reset_total,
)


# ---------------------------------------------------------------------------
# Fixture: isolate the global counter between tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_counter():
    reset_total()
    yield
    reset_total()


# ---------------------------------------------------------------------------
# estimate_video — rate math
# ---------------------------------------------------------------------------


def test_estimate_video_gen45_10s():
    assert estimate_video("gen4.5", 10) == 120  # 12 * 10


def test_estimate_video_gen45_5s():
    assert estimate_video("gen4.5", 5) == 60  # 12 * 5


def test_estimate_video_gen4_turbo_10s():
    assert estimate_video("gen4_turbo", 10) == 50  # 5 * 10


def test_estimate_video_gen4_turbo_5s():
    assert estimate_video("gen4_turbo", 5) == 25  # 5 * 5


def test_estimate_video_returns_int():
    result = estimate_video("gen4.5", 10)
    assert isinstance(result, int)


def test_estimate_video_invalid_model_raises():
    with pytest.raises(ValueError, match="Unknown video model"):
        estimate_video("gen3_alpha", 10)


def test_estimate_video_invalid_duration_raises():
    with pytest.raises(ValueError, match="Invalid video duration"):
        estimate_video("gen4.5", 7)


def test_estimate_video_zero_duration_raises():
    with pytest.raises(ValueError, match="Invalid video duration"):
        estimate_video("gen4.5", 0)


def test_estimate_video_15s_raises():
    with pytest.raises(ValueError, match="Invalid video duration"):
        estimate_video("gen4_turbo", 15)


# ---------------------------------------------------------------------------
# estimate_image — rate math
# ---------------------------------------------------------------------------


def test_estimate_image_turbo():
    assert estimate_image("gen4_image_turbo") == 2


def test_estimate_image_hd():
    assert estimate_image("gen4_image") == 8


def test_estimate_image_default_model():
    # Default should be gen4_image_turbo
    assert estimate_image() == IMAGE_CREDITS["gen4_image_turbo"]


def test_estimate_image_invalid_model_raises():
    with pytest.raises(ValueError, match="Unknown image model"):
        estimate_image("gen5_ultra")


# ---------------------------------------------------------------------------
# estimate_tts — rounding
# ---------------------------------------------------------------------------


def test_estimate_tts_exactly_50_chars():
    assert estimate_tts("a" * 50) == 1


def test_estimate_tts_one_char():
    # ceil(1 / 50) = 1
    assert estimate_tts("a") == 1


def test_estimate_tts_49_chars():
    assert estimate_tts("a" * 49) == 1


def test_estimate_tts_51_chars():
    # ceil(51 / 50) = 2
    assert estimate_tts("a" * 51) == 2


def test_estimate_tts_100_chars():
    # ceil(100 / 50) = 2
    assert estimate_tts("a" * 100) == 2


def test_estimate_tts_101_chars():
    # ceil(101 / 50) = 3
    assert estimate_tts("a" * 101) == 3


def test_estimate_tts_500_chars():
    # ceil(500 / 50) = 10
    assert estimate_tts("a" * 500) == 10


def test_estimate_tts_empty_string():
    # Empty text → 0 credits (no TTS call made)
    assert estimate_tts("") == 0


def test_estimate_tts_returns_int():
    assert isinstance(estimate_tts("hello world"), int)


def test_estimate_tts_realistic_script():
    # Typical voiceover ~90 words ≈ 550 chars; expect ceil(550/50) = 11
    script = (
        "Welcome back! We noticed you haven't visited us in a while. "
        "We have an exclusive offer just for you — thirty free spins on your "
        "favourite slots category. Your loyalty matters to us. Claim your bonus "
        "today and rediscover what you have been missing. This offer expires soon, "
        "so come back and enjoy the experience you love."
    )
    expected = -(-len(script) // TTS_CHARS_PER_CREDIT)  # ceiling division
    assert estimate_tts(script) == expected


# ---------------------------------------------------------------------------
# estimate_tts — brand sanitization before char-count
# ---------------------------------------------------------------------------


def test_estimate_tts_brand_stripped_before_counting():
    # "Starburst" (9 chars) → "abstract" (8 chars) after strip_forbidden.
    # Construct a string that is 51 chars with the brand but 50 chars after stripping:
    #   "Starburst" + "x"*42 = 9 + 42 = 51 chars  → 2 credits if unsanitized
    #   "abstract"  + "x"*42 = 8 + 42 = 50 chars  → 1 credit  after sanitized
    text = "Starburst" + "x" * 42
    assert estimate_tts(text) == 1


def test_estimate_tts_multiple_brands_stripped():
    # Two forbidden brands replaced with "abstract"; verifies strip is applied.
    # strip_forbidden may also collapse whitespace — derive expected from its output.
    from app.runway.prompt_safety import strip_forbidden

    text_with_brands = "Play at Starburst and NetEnt daily. " + "x" * 15
    sanitized = strip_forbidden(text_with_brands)
    expected = -(-len(sanitized) // TTS_CHARS_PER_CREDIT)
    assert estimate_tts(text_with_brands) == expected


# ---------------------------------------------------------------------------
# estimate_video_plan — aggregate totals
# ---------------------------------------------------------------------------


def test_plan_4_scenes_gen45_10s_with_images_no_tts():
    # video: 4 * 120 = 480, images: 4 * 2 = 8, tts: 0, total: 488
    plan = estimate_video_plan(scene_count=4)
    assert plan["video"] == 480
    assert plan["images"] == 8
    assert plan["tts"] == 0
    assert plan["total"] == 488


def test_plan_3_scenes_gen4_turbo_5s():
    # video: 3 * 25 = 75, images: 3 * 2 = 6, tts: 0, total: 81
    plan = estimate_video_plan(
        scene_count=3,
        video_model="gen4_turbo",
        duration_sec=5,
    )
    assert plan["video"] == 75
    assert plan["images"] == 6
    assert plan["tts"] == 0
    assert plan["total"] == 81


def test_plan_no_images():
    plan = estimate_video_plan(scene_count=4, include_images=False)
    assert plan["images"] == 0
    assert plan["total"] == plan["video"] + plan["tts"]


def test_plan_with_tts():
    # 50-char voiceover → 1 credit TTS
    plan = estimate_video_plan(scene_count=4, tts_text="a" * 50)
    assert plan["tts"] == 1
    assert plan["total"] == plan["video"] + plan["images"] + 1


def test_plan_total_equals_sum_of_parts():
    plan = estimate_video_plan(
        scene_count=5,
        video_model="gen4.5",
        duration_sec=10,
        image_model="gen4_image",
        tts_text="x" * 200,
        include_images=True,
    )
    assert plan["total"] == plan["video"] + plan["images"] + plan["tts"]


def test_plan_empty_tts_text_gives_zero_tts():
    plan = estimate_video_plan(scene_count=2, tts_text="")
    assert plan["tts"] == 0


def test_plan_invalid_video_model_raises():
    with pytest.raises(ValueError, match="Unknown video model"):
        estimate_video_plan(scene_count=4, video_model="gen99_ultra")


def test_plan_invalid_duration_raises():
    with pytest.raises(ValueError, match="Invalid video duration"):
        estimate_video_plan(scene_count=4, duration_sec=3)


def test_plan_invalid_image_model_raises():
    with pytest.raises(ValueError, match="Unknown image model"):
        estimate_video_plan(scene_count=4, image_model="gen99_image")


def test_plan_returns_all_keys():
    plan = estimate_video_plan(scene_count=1)
    assert set(plan.keys()) == {"video", "images", "tts", "total"}


def test_plan_one_scene_gen45_10s():
    # Matches RUNWAY_API_CHEATSHEET "Финальный батч" row: 7 × 4 × 10 × 12 = 3360
    # Single unit: 1 scene × 10s × 12 credits = 120 video + 2 image = 122
    plan = estimate_video_plan(scene_count=1, video_model="gen4.5", duration_sec=10)
    assert plan["video"] == 120
    assert plan["images"] == 2
    assert plan["total"] == 122


def test_plan_cheatsheet_final_batch():
    # RUNWAY_API_CHEATSHEET: 7 campaigns × 4 scenes × 10s gen4.5 = 3360 video credits
    # + 7 × 4 images = 56 image credits (cheatsheet omits this)
    # We test only video portion matches
    total_video = sum(
        estimate_video_plan(scene_count=4, video_model="gen4.5", duration_sec=10)["video"]
        for _ in range(7)
    )
    assert total_video == 3360


# ---------------------------------------------------------------------------
# Counter: reset / increment
# ---------------------------------------------------------------------------


def test_counter_starts_at_zero():
    assert get_total() == 0


def test_add_to_total_increments():
    add_to_total(100)
    assert get_total() == 100


def test_add_to_total_cumulative():
    add_to_total(100)
    add_to_total(50)
    assert get_total() == 150


def test_reset_total_clears_counter():
    add_to_total(200)
    reset_total()
    assert get_total() == 0


def test_multiple_add_reset_cycle():
    add_to_total(120)
    add_to_total(60)
    reset_total()
    add_to_total(25)
    assert get_total() == 25


def test_counter_workflow_with_estimate():
    credits = estimate_video("gen4.5", 10)  # 120
    add_to_total(credits)
    credits2 = estimate_image("gen4_image_turbo")  # 2
    add_to_total(credits2)
    assert get_total() == 122


# ---------------------------------------------------------------------------
# Constants sanity
# ---------------------------------------------------------------------------


def test_video_rate_constants():
    assert VIDEO_CREDITS_PER_SEC["gen4.5"] == 12
    assert VIDEO_CREDITS_PER_SEC["gen4_turbo"] == 5


def test_image_rate_constants():
    assert IMAGE_CREDITS["gen4_image_turbo"] == 2
    assert IMAGE_CREDITS["gen4_image"] == 8


def test_tts_chars_per_credit():
    assert TTS_CHARS_PER_CREDIT == 50


def test_valid_durations():
    assert 5 in VALID_VIDEO_DURATIONS
    assert 10 in VALID_VIDEO_DURATIONS
    assert 7 not in VALID_VIDEO_DURATIONS

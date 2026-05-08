"""Tests for app.runway.prompt_safety — no Runway network calls."""
from __future__ import annotations

import pytest

from app.runway.prompt_safety import build_safe_visual_prompt, sanitize_visual_brief, strip_forbidden
from app.runway.visual_hints import (
    CATEGORY_VISUAL_HINTS,
    DEFAULT_VISUAL_HINT,
    GAME_VISUAL_HINTS,
)


# ---------------------------------------------------------------------------
# strip_forbidden
# ---------------------------------------------------------------------------


class TestStripForbidden:
    def test_removes_pragmatic_play(self):
        result = strip_forbidden("Pragmatic Play slot with cinematic glow")
        assert "Pragmatic Play" not in result
        assert "pragmatic play" not in result.lower()

    def test_removes_netent(self):
        result = strip_forbidden("NetEnt game visuals")
        assert "netent" not in result.lower()

    def test_removes_bet365(self):
        result = strip_forbidden("Bet365 branded motion")
        assert "bet365" not in result.lower()

    def test_removes_game_title_book_of_dead(self):
        result = strip_forbidden("Book of Dead scatter symbols")
        assert "book of dead" not in result.lower()

    def test_removes_starburst(self):
        result = strip_forbidden("Starburst wilds expanding")
        assert "starburst" not in result.lower()

    def test_removes_gates_of_olympus(self):
        result = strip_forbidden("Gates of Olympus multiplier drop")
        assert "gates of olympus" not in result.lower()

    def test_removes_real_face(self):
        result = strip_forbidden("cinematic scene with real face in foreground")
        assert "real face" not in result.lower()

    def test_removes_celebrity(self):
        result = strip_forbidden("celebrity endorsement background")
        assert "celebrity" not in result.lower()

    def test_removes_portrait(self):
        result = strip_forbidden("close-up portrait of a person")
        assert "portrait" not in result.lower()

    def test_removes_human_face(self):
        result = strip_forbidden("human face overlay")
        assert "human face" not in result.lower()

    def test_case_insensitive(self):
        result = strip_forbidden("PRAGMATIC PLAY SLOT")
        assert "pragmatic play" not in result.lower()

    def test_preserves_safe_content(self):
        safe = "abstract reel shapes, soft golden particles, dark backdrop, no text, no logos"
        result = strip_forbidden(safe)
        assert result == safe

    def test_no_double_spaces(self):
        result = strip_forbidden("Bet365 and NetEnt slot")
        assert "  " not in result

    def test_multiple_brands_replaced(self):
        result = strip_forbidden("Pragmatic Play and NetEnt both produce Starburst style games")
        assert "pragmatic play" not in result.lower()
        assert "netent" not in result.lower()
        assert "starburst" not in result.lower()


# ---------------------------------------------------------------------------
# sanitize_visual_brief
# ---------------------------------------------------------------------------


class TestSanitizeVisualBrief:
    def test_xlsx_dod_example(self):
        result = sanitize_visual_brief("Pragmatic Play slot with face")
        assert "Pragmatic Play" not in result
        assert "face" not in result.lower() or "no text" in result.lower()
        assert "no text" in result
        assert "no logos" in result

    def test_adds_no_text_no_logos_when_missing(self):
        result = sanitize_visual_brief("abstract reel shapes")
        assert "no text" in result
        assert "no logos" in result

    def test_does_not_duplicate_no_text_no_logos(self):
        brief = "abstract reel shapes, cinematic dark backdrop, no text, no logos"
        result = sanitize_visual_brief(brief)
        assert result.count("no text") == 1
        assert result.count("no logos") == 1

    def test_igaming_safe_mode_tail(self):
        result = sanitize_visual_brief("abstract motion", mode="igaming_safe")
        assert "cinematic dark backdrop" in result
        assert "no text" in result
        assert "no logos" in result

    def test_generic_subscription_mode_tail(self):
        result = sanitize_visual_brief("abstract motion", mode="generic_subscription")
        assert "premium lifestyle" in result
        assert "no text" in result
        assert "no logos" in result

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="Unknown visual mode"):
            sanitize_visual_brief("abstract motion", mode="unknown_mode")  # type: ignore[arg-type]

    def test_strips_brand_and_adds_suffix(self):
        result = sanitize_visual_brief("NetEnt game background")
        assert "netent" not in result.lower()
        assert "no text" in result
        assert "no logos" in result

    def test_empty_string_returns_mode_tail(self):
        result = sanitize_visual_brief("", mode="igaming_safe")
        assert "no text" in result
        assert "no logos" in result

    def test_already_safe_prompt_unchanged_except_casing(self):
        safe = "abstract reel shapes, cinematic dark backdrop, no text, no logos"
        result = sanitize_visual_brief(safe)
        assert "no text" in result
        assert "no logos" in result
        assert "abstract" in result


# ---------------------------------------------------------------------------
# build_safe_visual_prompt
# ---------------------------------------------------------------------------


class TestBuildSafeVisualPrompt:
    def test_known_game_label_uses_b04_hint(self):
        result = build_safe_visual_prompt(game_label="neon_spins")
        assert "neon" in result.lower() or "electric" in result.lower()
        assert "no text" in result
        assert "no logos" in result

    def test_known_category_falls_back_to_category_hint(self):
        result = build_safe_visual_prompt(game_label="unknown_game", game_category="slots")
        expected_fragment = CATEGORY_VISUAL_HINTS["slots"].split(",")[0]
        assert expected_fragment.strip().lower() in result.lower()

    def test_unknown_label_and_category_uses_default(self):
        result = build_safe_visual_prompt(game_label="x", game_category="y")
        assert DEFAULT_VISUAL_HINT.split(",")[0].strip().lower() in result.lower()

    def test_no_args_uses_default_hint(self):
        result = build_safe_visual_prompt()
        assert DEFAULT_VISUAL_HINT.split(",")[0].strip().lower() in result.lower()

    def test_extra_brief_is_sanitized_and_appended(self):
        result = build_safe_visual_prompt(
            game_label="classic_roulette",
            extra_brief="Pragmatic Play logo in corner",
        )
        assert "Pragmatic Play" not in result
        assert "pragmatic play" not in result.lower()
        assert "no text" in result
        assert "no logos" in result

    def test_extra_brief_clean_is_appended(self):
        result = build_safe_visual_prompt(
            game_label="fruit_slots",
            extra_brief="warm amber glow from left",
        )
        assert "warm amber glow from left" in result
        assert "no text" in result

    def test_all_game_labels_from_b04_produce_safe_prompts(self):
        for label in GAME_VISUAL_HINTS:
            result = build_safe_visual_prompt(game_label=label)
            assert "no text" in result, f"Missing 'no text' for label {label!r}"
            assert "no logos" in result, f"Missing 'no logos' for label {label!r}"

    def test_all_categories_from_b04_produce_safe_prompts(self):
        for category in CATEGORY_VISUAL_HINTS:
            result = build_safe_visual_prompt(game_category=category)
            assert "no text" in result, f"Missing 'no text' for category {category!r}"
            assert "no logos" in result, f"Missing 'no logos' for category {category!r}"

    def test_generic_subscription_mode(self):
        result = build_safe_visual_prompt(
            game_label=None,
            mode="generic_subscription",
        )
        assert "no text" in result
        assert "no logos" in result

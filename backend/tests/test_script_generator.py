"""Tests for script_generator — no network calls.

All LLM interactions are replaced with lightweight fakes that implement
the LLMClient protocol.
"""
from __future__ import annotations

import json

import pytest

import app.agent.script_generator as script_generator
from app.agent.script_generator import generate_script
from app.models import Player

# ── Shared fixtures ────────────────────────────────────────────────────────

OFFER = "50 free spins on your favourite game"


def _player(
    player_id: str = "p_test",
    first_name: str = "Lucas",
    country: str = "BR",
    currency: str = "BRL",
    cohort: str = "high_value_dormant",
    game_label: str | None = "fruit_slots",
    game_category: str | None = "slots",
) -> Player:
    return Player(
        player_id=player_id,
        external_id=player_id,
        first_name=first_name,
        country=country,
        currency=currency,
        favorite_game_label=game_label,
        favorite_game_category=game_category,
    )


def _valid_script_json(first_name: str = "Lucas", offer: str = OFFER) -> str:
    data = {
        "scenes": [
            {"id": 1, "type": "intro",             "text": f"Hello {first_name}, we have something for you.", "visual_brief": "abstract motion, no text, no logos"},
            {"id": 2, "type": "personalized_hook",  "text": "Based on your favourite slots activity.",        "visual_brief": "soft reel shapes, no text, no logos"},
            {"id": 3, "type": "offer",              "text": f"We prepared: {offer}.",                         "visual_brief": "golden particle burst, no text, no logos"},
            {"id": 4, "type": "cta",               "text": "Come back and enjoy.",                            "visual_brief": "warm glow, no text, no logos"},
        ],
        "full_voiceover_text": (
            f"Hello {first_name}, we have something for you. "
            "Based on your favourite slots activity we built this message just for you. "
            f"We prepared {offer} as a warm welcome back. "
            "Come back and enjoy whenever you feel ready."
        ),
        "estimated_duration_sec": 38,
        "tone": "warm",
        "cta_text": "see your offer",
    }
    return json.dumps(data)


# ── Minimal LLM fakes ──────────────────────────────────────────────────────

class _MockLLM:
    """Returns a fixed string from generate()."""

    def __init__(self, response: str) -> None:
        self._response = response

    def generate(self, system: str, user: str) -> str:  # noqa: ARG002
        return self._response


class _RaisingLLM:
    """Always raises from generate()."""

    def generate(self, system: str, user: str) -> str:  # noqa: ARG002
        raise RuntimeError("simulated LLM failure")


@pytest.fixture(autouse=True)
def _disable_default_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep tests offline even when ANTHROPIC_API_KEY exists locally."""
    monkeypatch.setattr(script_generator, "_make_client", lambda: None)


# ── Happy path ─────────────────────────────────────────────────────────────

def test_happy_path_returns_llm_source() -> None:
    p = _player()
    result = generate_script(p, "high_value_dormant", OFFER, llm=_MockLLM(_valid_script_json()))
    assert result["source"] == "llm"


def test_happy_path_has_4_scenes() -> None:
    p = _player()
    result = generate_script(p, "high_value_dormant", OFFER, llm=_MockLLM(_valid_script_json()))
    assert len(result["scenes"]) == 4


def test_happy_path_scene_types_in_order() -> None:
    p = _player()
    result = generate_script(p, "high_value_dormant", OFFER, llm=_MockLLM(_valid_script_json()))
    types = [s["type"] for s in result["scenes"]]
    assert types == ["intro", "personalized_hook", "offer", "cta"]


def test_happy_path_scene_ids_sequential() -> None:
    p = _player()
    result = generate_script(p, "high_value_dormant", OFFER, llm=_MockLLM(_valid_script_json()))
    ids = [s["id"] for s in result["scenes"]]
    assert ids == [1, 2, 3, 4]


def test_happy_path_voiceover_non_empty() -> None:
    p = _player()
    result = generate_script(p, "high_value_dormant", OFFER, llm=_MockLLM(_valid_script_json()))
    assert result["full_voiceover_text"].strip()


def test_happy_path_cta_text_present() -> None:
    p = _player()
    result = generate_script(p, "high_value_dormant", OFFER, llm=_MockLLM(_valid_script_json()))
    assert result["cta_text"]


def test_happy_path_result_is_script_dict() -> None:
    p = _player()
    result = generate_script(p, "high_value_dormant", OFFER, llm=_MockLLM(_valid_script_json()))
    # ScriptDict has all required keys
    for key in ("scenes", "full_voiceover_text", "estimated_duration_sec", "tone", "cta_text", "source"):
        assert key in result, f"missing key: {key}"


# ── Fallback: LLM unavailable ──────────────────────────────────────────────

def test_fallback_when_no_llm() -> None:
    """llm=None with no default client → fallback."""
    p = _player()
    result = generate_script(p, "high_value_dormant", OFFER, llm=None)
    assert result["source"] == "fallback"


def test_fallback_when_llm_raises() -> None:
    p = _player()
    result = generate_script(p, "high_value_dormant", OFFER, llm=_RaisingLLM())
    assert result["source"] == "fallback"


# ── Fallback: invalid/malformed LLM output ─────────────────────────────────

def test_fallback_on_invalid_json() -> None:
    p = _player()
    result = generate_script(p, "casual_dormant", OFFER, llm=_MockLLM("not json at all"))
    assert result["source"] == "fallback"


def test_fallback_on_empty_response() -> None:
    p = _player()
    result = generate_script(p, "casual_dormant", OFFER, llm=_MockLLM(""))
    assert result["source"] == "fallback"


def test_fallback_on_wrong_scene_count() -> None:
    data = json.loads(_valid_script_json())
    data["scenes"] = data["scenes"][:3]  # only 3 scenes
    p = _player()
    result = generate_script(p, "casual_dormant", OFFER, llm=_MockLLM(json.dumps(data)))
    assert result["source"] == "fallback"


def test_fallback_on_missing_scenes_key() -> None:
    data = {"full_voiceover_text": "hello", "tone": "warm", "cta_text": "go"}
    p = _player()
    result = generate_script(p, "casual_dormant", OFFER, llm=_MockLLM(json.dumps(data)))
    assert result["source"] == "fallback"


def test_fallback_on_wrong_scene_type_order() -> None:
    data = json.loads(_valid_script_json())
    data["scenes"][0]["type"] = "cta"  # wrong order
    p = _player()
    result = generate_script(p, "casual_dormant", OFFER, llm=_MockLLM(json.dumps(data)))
    assert result["source"] == "fallback"


def test_fallback_on_missing_scene_text_key() -> None:
    data = json.loads(_valid_script_json())
    del data["scenes"][1]["text"]
    p = _player()
    result = generate_script(p, "casual_dormant", OFFER, llm=_MockLLM(json.dumps(data)))
    assert result["source"] == "fallback"


# ── Fallback: forbidden terms ──────────────────────────────────────────────

@pytest.mark.parametrize("bad_term", [
    "guaranteed",
    "don't miss",
    "last chance",
    "you will definitely win",
])
def test_fallback_on_forbidden_term_in_voiceover(bad_term: str) -> None:
    data = json.loads(_valid_script_json())
    data["full_voiceover_text"] += f" This offer is {bad_term}."
    p = _player()
    result = generate_script(p, "casual_dormant", OFFER, llm=_MockLLM(json.dumps(data)))
    assert result["source"] == "fallback"


def test_fallback_on_forbidden_term_in_scene_text() -> None:
    data = json.loads(_valid_script_json())
    data["scenes"][2]["text"] = "This offer is guaranteed to impress."
    p = _player()
    result = generate_script(p, "casual_dormant", OFFER, llm=_MockLLM(json.dumps(data)))
    assert result["source"] == "fallback"


# ── Fallback: placeholder rendering ───────────────────────────────────────

def test_fallback_renders_first_name() -> None:
    p = _player(first_name="Ingrid")
    result = generate_script(p, "vip_at_risk", OFFER, llm=None)
    all_text = " ".join(s["text"] for s in result["scenes"])
    assert "Ingrid" in all_text, "first_name placeholder not rendered in fallback"


def test_fallback_renders_offer_value() -> None:
    p = _player()
    result = generate_script(p, "casual_dormant", OFFER, llm=None)
    all_text = " ".join(s["text"] for s in result["scenes"]) + result["full_voiceover_text"]
    assert OFFER in all_text, "offer_value placeholder not rendered in fallback"


def test_fallback_no_unreplaced_placeholders() -> None:
    p = _player()
    result = generate_script(p, "lapsed_loyal", OFFER, llm=None)
    all_text = (
        " ".join(s["text"] for s in result["scenes"])
        + result["full_voiceover_text"]
        + result["cta_text"]
    )
    assert "{" not in all_text and "}" not in all_text, (
        f"Unreplaced placeholders found: {all_text}"
    )


def test_fallback_has_4_scenes() -> None:
    p = _player()
    result = generate_script(p, "post_event", OFFER, llm=None)
    assert len(result["scenes"]) == 4


def test_fallback_covers_all_6_cohorts() -> None:
    cohorts = [
        "casual_dormant",
        "high_value_dormant",
        "post_event",
        "first_deposit_no_return",
        "vip_at_risk",
        "lapsed_loyal",
    ]
    p = _player()
    for cohort in cohorts:
        result = generate_script(p, cohort, OFFER, llm=None)
        assert result["source"] == "fallback"
        assert len(result["scenes"]) == 4


def test_fallback_unknown_cohort_uses_default() -> None:
    p = _player()
    result = generate_script(p, "nonexistent_cohort", OFFER, llm=None)
    assert result["source"] == "fallback"
    assert len(result["scenes"]) == 4


# ── LLM output in markdown fences is accepted ─────────────────────────────

def test_json_in_markdown_fence_accepted() -> None:
    raw = "```json\n" + _valid_script_json() + "\n```"
    p = _player()
    result = generate_script(p, "high_value_dormant", OFFER, llm=_MockLLM(raw))
    assert result["source"] == "llm"


def test_json_with_preamble_accepted() -> None:
    raw = "Sure! Here is the script:\n" + _valid_script_json()
    p = _player()
    result = generate_script(p, "high_value_dormant", OFFER, llm=_MockLLM(raw))
    assert result["source"] == "llm"

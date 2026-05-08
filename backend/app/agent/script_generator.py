"""Script generator — LLM path with B-03 fallback.

Entry point: generate_script(player, cohort, offer, llm=None) -> ScriptDict

LLM is injected via the LLMClient protocol so tests never call the network.
All failure modes (no key, network error, bad JSON, wrong shape, forbidden
terms) silently fall back to the B-03 fallback_templates.
"""
from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Protocol, TypedDict

from app.agent.fallback_templates import FALLBACK_TEMPLATES
from app.agent.prompts import (
    FORBIDDEN_TEXT_TERMS,
    SYSTEM_PROMPT,
    build_user_prompt,
)
from app.runway.prompt_safety import sanitize_visual_brief
from app.runway.visual_hints import get_visual_hint

if TYPE_CHECKING:
    from app.models import Player

# ── Public output types ────────────────────────────────────────────────────


class SceneDict(TypedDict):
    id: int
    type: str
    text: str
    visual_brief: str


class ScriptDict(TypedDict):
    scenes: list[SceneDict]
    full_voiceover_text: str
    estimated_duration_sec: int
    tone: str
    cta_text: str
    source: str  # "llm" | "fallback"


# ── LLM boundary ───────────────────────────────────────────────────────────


class LLMClient(Protocol):
    def generate(self, system: str, user: str) -> str:
        ...


class AnthropicLLMClient:
    """Thin wrapper around the Anthropic Messages API."""

    _MODEL = "claude-sonnet-4-5"

    def __init__(self) -> None:
        from app.config import settings

        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        import anthropic

        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def generate(self, system: str, user: str) -> str:
        resp = self._client.messages.create(
            model=self._MODEL,
            max_tokens=1200,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text  # type: ignore[union-attr]


def _make_client() -> LLMClient | None:
    try:
        return AnthropicLLMClient()
    except Exception:
        return None


# ── Validation helpers ─────────────────────────────────────────────────────

_REQUIRED_SCENE_KEYS = {"id", "type", "text", "visual_brief"}
_EXPECTED_SCENE_TYPES = ("intro", "personalized_hook", "offer", "cta")


def _has_forbidden_text(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in FORBIDDEN_TEXT_TERMS)


def _extract_json(raw: str) -> dict | None:
    """Return the first JSON object found in *raw*, or None."""
    raw = raw.strip()
    # Try direct parse first.
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    # Strip markdown code fences.
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if fenced:
        try:
            obj = json.loads(fenced.group(1))
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
    # Last resort: grab outermost braces.
    bare = re.search(r"\{.*\}", raw, re.DOTALL)
    if bare:
        try:
            obj = json.loads(bare.group())
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
    return None


def _validate(data: dict) -> ScriptDict | None:
    """Return a validated ScriptDict or None if any check fails."""
    scenes_raw = data.get("scenes")
    if not isinstance(scenes_raw, list) or len(scenes_raw) != 4:
        return None

    scenes: list[SceneDict] = []
    for i, s in enumerate(scenes_raw):
        if not isinstance(s, dict) or not _REQUIRED_SCENE_KEYS.issubset(s):
            return None
        expected_type = _EXPECTED_SCENE_TYPES[i]
        if s.get("type") != expected_type:
            return None
        scenes.append(
            SceneDict(
                id=int(s["id"]),
                type=str(s["type"]),
                text=str(s["text"]),
                visual_brief=sanitize_visual_brief(str(s["visual_brief"])),
            )
        )

    voiceover = str(data.get("full_voiceover_text", ""))
    if not voiceover:
        return None

    # Check forbidden terms in all text content.
    all_text = voiceover + " " + " ".join(s["text"] for s in scenes)
    if _has_forbidden_text(all_text):
        return None

    return ScriptDict(
        scenes=scenes,
        full_voiceover_text=voiceover,
        estimated_duration_sec=int(data.get("estimated_duration_sec", 38)),
        tone=str(data.get("tone", "warm")),
        cta_text=str(data.get("cta_text", "see your offer")),
        source="llm",
    )


# ── Fallback rendering ─────────────────────────────────────────────────────

_DEFAULT_COHORT = "casual_dormant"
_DEFAULT_CTA = "see your personal offer"


def _render(template: str, ctx: dict[str, str]) -> str:
    for key, value in ctx.items():
        template = template.replace(f"{{{key}}}", value)
    return template


def _fallback(player: Player, cohort: str, offer: str) -> ScriptDict:
    tmpl = FALLBACK_TEMPLATES.get(cohort) or FALLBACK_TEMPLATES[_DEFAULT_COHORT]
    visual_hint = get_visual_hint(player.favorite_game_label, player.favorite_game_category)
    cta_text = _DEFAULT_CTA

    ctx: dict[str, str] = {
        "first_name": player.first_name,
        "offer_value": offer,
        "favorite_game_visual_hint": visual_hint,
        "cta": cta_text,
    }

    scenes: list[SceneDict] = []
    for raw_scene in tmpl["scenes"]:
        scenes.append(
            SceneDict(
                id=int(raw_scene["id"]),
                type=str(raw_scene["type"]),
                text=_render(str(raw_scene["text"]), ctx),
                visual_brief=_render(str(raw_scene["visual_brief"]), ctx),
            )
        )

    return ScriptDict(
        scenes=scenes,
        full_voiceover_text=_render(str(tmpl["full_voiceover_text"]), ctx),
        estimated_duration_sec=int(tmpl.get("estimated_duration_sec", 38)),
        tone=str(tmpl.get("tone", "warm")),
        cta_text=_render(str(tmpl.get("cta_text", "{cta}")), ctx),
        source="fallback",
    )


# ── Public entry point ─────────────────────────────────────────────────────


def generate_script(
    player: Player,
    cohort: str,
    offer: str,
    llm: LLMClient | None = None,
) -> ScriptDict:
    """Generate a 4-scene script for *player*.

    *llm* is injected for testing.  When None, attempts to build an
    AnthropicLLMClient from settings; any failure falls through to the
    B-03 fallback templates.
    """
    client: LLMClient | None = llm if llm is not None else _make_client()

    if client is not None:
        try:
            user_prompt = build_user_prompt(
                first_name=player.first_name,
                country=player.country or "",
                currency=player.currency or "",
                cohort=cohort,
                offer=offer,
                game_label=player.favorite_game_label,
                game_category=player.favorite_game_category,
            )
            raw = client.generate(SYSTEM_PROMPT, user_prompt)
            data = _extract_json(raw)
            if data is not None:
                validated = _validate(data)
                if validated is not None:
                    return validated
        except Exception:
            pass  # any error → fallback

    return _fallback(player, cohort, offer)

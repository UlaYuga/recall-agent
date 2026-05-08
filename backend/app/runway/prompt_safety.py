"""Pre-flight prompt sanitizer for all Runway image/video requests.

Rules enforced here must be verified before every RunwayClient call.
Safety failures must never be retried with the original unsafe prompt.
"""
from __future__ import annotations

import re
from typing import Literal

from app.runway.visual_hints import get_visual_hint

VisualMode = Literal["igaming_safe", "generic_subscription"]

# ---------------------------------------------------------------------------
# Forbidden content lists
# ---------------------------------------------------------------------------

# Real iGaming operators, providers, sportsbooks and game studios.
_FORBIDDEN_BRANDS: tuple[str, ...] = (
    "Pragmatic Play",
    "NetEnt",
    "Net Entertainment",
    "Microgaming",
    "Play'n GO",
    "Play n GO",
    "Playngo",
    "Evolution Gaming",
    "Evolution",
    "Playtech",
    "Yggdrasil",
    "Novomatic",
    "Aristocrat",
    "Blueprint Gaming",
    "Red Tiger",
    "Big Time Gaming",
    "Hacksaw Gaming",
    "Nolimit City",
    "Push Gaming",
    "Relax Gaming",
    "Quickspin",
    "Thunderkick",
    "Elk Studios",
    "Betsoft",
    "Bet365",
    "William Hill",
    "Betway",
    "PokerStars",
    "888casino",
    "888 Casino",
    "Paddy Power",
    "Ladbrokes",
    "Coral",
    "Mr Green",
    "LeoVegas",
    "Betsson",
    "Unibet",
    "Kindred",
    "Parimatch",
    "1xBet",
    "Bwin",
    "Pinnacle",
    "FanDuel",
    "DraftKings",
    "BetMGM",
    "Hard Rock",
    "Caesars",
    "BetVictor",
)

# Well-known game titles whose names carry brand/IP risk.
_FORBIDDEN_GAME_TITLES: tuple[str, ...] = (
    "Book of Dead",
    "Book of Ra",
    "Legacy of Dead",
    "Starburst",
    "Gates of Olympus",
    "Sweet Bonanza",
    "Wolf Gold",
    "Gonzo's Quest",
    "Dead or Alive",
    "Divine Fortune",
    "Mega Moolah",
    "Monopoly Live",
    "Lightning Roulette",
    "Crazy Time",
    "Reactoonz",
    "Fire Joker",
    "Blood Suckers",
    "Jack Hammer",
    "Twin Spin",
    "Bonanza",
)

# Patterns that describe real faces or people.
_FORBIDDEN_FACE_PATTERNS: tuple[str, ...] = (
    r"\breal\s+face\b",
    r"\breal\s+person\b",
    r"\breal\s+people\b",
    r"\bcelebrity\b",
    r"\bcelebrities\b",
    r"\blikeness\b",
    r"\bportrait\b",
    r"\bhuman\s+face\b",
    r"\bhuman\s+figure\b",
    r"\bphotorealistic\s+person\b",
    r"\bphotorealistic\s+face\b",
    r"\brecognizable\s+person\b",
)

# ---------------------------------------------------------------------------
# Compiled replacement table (built once at import time)
# ---------------------------------------------------------------------------

# Each entry is (compiled_pattern, safe_replacement)
_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = []


def _build():
    for brand in (*_FORBIDDEN_BRANDS, *_FORBIDDEN_GAME_TITLES):
        _REPLACEMENTS.append((re.compile(re.escape(brand), re.IGNORECASE), "abstract"))
    for pat in _FORBIDDEN_FACE_PATTERNS:
        _REPLACEMENTS.append((re.compile(pat, re.IGNORECASE), "abstract element"))


_build()

# ---------------------------------------------------------------------------
# Mode-specific safety tails
# ---------------------------------------------------------------------------

_MODE_TAIL: dict[str, str] = {
    "igaming_safe": "abstract motion graphics, cinematic dark backdrop, no text, no logos",
    "generic_subscription": "abstract premium lifestyle, soft light, minimal composition, no text, no logos",
}

# Safety markers that must be present in every prompt sent to Runway.
_REQUIRED_MARKERS: tuple[str, str] = ("no text", "no logos")

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def strip_forbidden(text: str) -> str:
    """Replace forbidden brand names, game titles, and face references with safe abstractions.

    Does not add safety suffixes — use :func:`sanitize_visual_brief` for full sanitization.
    """
    result = text
    for pattern, replacement in _REPLACEMENTS:
        result = pattern.sub(replacement, result)
    # Collapse runs of whitespace and stray commas produced by substitutions.
    result = re.sub(r"\s{2,}", " ", result)
    result = re.sub(r",\s*,", ",", result)
    return result.strip()


def sanitize_visual_brief(brief: str, *, mode: VisualMode = "igaming_safe") -> str:
    """Return a Runway-safe visual prompt.

    1. Strips forbidden brand/face/person references.
    2. Ensures the required 'no text, no logos' markers are present.
    3. Appends the mode-specific safety tail if neither marker is already in the text.
    """
    if mode not in _MODE_TAIL:
        raise ValueError(f"Unknown visual mode {mode!r}. Expected one of: {list(_MODE_TAIL)}")

    cleaned = strip_forbidden(brief)

    missing = [m for m in _REQUIRED_MARKERS if m not in cleaned.lower()]
    if missing:
        tail = _MODE_TAIL[mode]
        cleaned = f"{cleaned}, {tail}" if cleaned else tail

    return cleaned


def build_safe_visual_prompt(
    game_label: str | None = None,
    game_category: str | None = None,
    extra_brief: str = "",
    *,
    mode: VisualMode = "igaming_safe",
) -> str:
    """Compose a fully safe Runway visual prompt from B-04 hints and optional extra text.

    Lookup order: GAME_VISUAL_HINTS → CATEGORY_VISUAL_HINTS → DEFAULT_VISUAL_HINT.
    Any extra_brief text is sanitized and appended.
    """
    base = get_visual_hint(game_label, game_category)

    if extra_brief:
        safe_extra = sanitize_visual_brief(extra_brief, mode=mode)
        prompt = f"{base}, {safe_extra}"
    else:
        prompt = base

    # Base hints from B-04 already contain 'no text, no logos', but run through
    # sanitizer to guarantee consistency if hints ever change.
    return sanitize_visual_brief(prompt, mode=mode)

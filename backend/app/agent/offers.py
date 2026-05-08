"""Deterministic offer rules engine.

Maps classifier cohorts to structured offers.  No LLM, no DB, no API calls.
Output is stable: identical inputs always produce identical offers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import Player

# ---------------------------------------------------------------------------
# Offer bands — match TECH_SPEC recommended_offer_band vocabulary
# ---------------------------------------------------------------------------
OFFER_BANDS = frozenset(
    {
        "free_spins_small",
        "free_spins_mid",
        "deposit_match_low",
        "deposit_match_high",
        "cashback",
        "free_bet",
        "personal_manager_call",
    }
)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Offer:
    """Structured offer returned by the rules engine.

    Fields
    ------
    type:        Machine-readable kind (free_spins | deposit_match | cashback |
                 free_bet | personal_manager_call).
    value:       Numeric value — spins count, match %, cashback %, or free-bet
                 credit amount.  Zero for personal_manager_call.
    label:       Short human-readable offer name for UI display.
    copy:        Full marketing copy suitable for script template {offer_value}.
    terms:       T&C snippet appended to any regulated communication.
    expiry_days: Calendar days until the offer expires from issuance.
    offer_band:  TECH_SPEC band string for downstream routing.
    game_label:  Preferred game slug for free_spins offers; None otherwise.
    cohort:      Source cohort — preserved for audit and serialization.
    """

    type: str
    value: int | float
    label: str
    copy: str
    terms: str
    expiry_days: int
    offer_band: str
    cohort: str
    game_label: str | None = None


# ---------------------------------------------------------------------------
# Per-cohort defaults (deterministic, no runtime randomness)
# ---------------------------------------------------------------------------

_DEFAULT_FREE_SPINS_GAME = "classic_roulette"

_COHORT_DEFAULTS: dict[str, dict] = {
    "vip_at_risk": {
        "type": "deposit_match",
        "value": 100,
        "label": "100% Deposit Match",
        "copy": "100% deposit match up to your personal limit — available this week only",
        "terms": "Match bonus credited on next deposit. Wagering requirement applies. Valid for 7 days.",
        "expiry_days": 7,
        "offer_band": "deposit_match_high",
        "game_label": None,
    },
    "high_value_dormant": {
        "type": "cashback",
        "value": 15,
        "label": "15% Cashback",
        "copy": "15% cashback on your next session — a personal thank-you for being a valued player",
        "terms": "Cashback applied to net losses in the qualifying session. Valid for 10 days.",
        "expiry_days": 10,
        "offer_band": "cashback",
        "game_label": None,
    },
    "lapsed_loyal": {
        "type": "free_spins",
        "value": 50,
        "label": "50 Free Spins",
        "copy": "50 free spins waiting for you — no deposit required",
        "terms": "Free spins valid on selected games. Winnings subject to wagering. Valid for 14 days.",
        "expiry_days": 14,
        "offer_band": "free_spins_mid",
        "game_label": _DEFAULT_FREE_SPINS_GAME,
    },
    "post_event": {
        "type": "free_bet",
        "value": 10,
        "label": "€10 Free Bet",
        "copy": "€10 free bet — pick your next event and jump back in",
        "terms": "Free bet stake not returned. Single use. Valid for 7 days.",
        "expiry_days": 7,
        "offer_band": "free_bet",
        "game_label": None,
    },
    "first_deposit_no_return": {
        "type": "free_spins",
        "value": 20,
        "label": "20 Free Spins",
        "copy": "20 free spins — take another look at no extra cost",
        "terms": "Free spins valid on selected games. Winnings subject to wagering. Valid for 14 days.",
        "expiry_days": 14,
        "offer_band": "free_spins_small",
        "game_label": _DEFAULT_FREE_SPINS_GAME,
    },
    "casual_dormant": {
        "type": "free_spins",
        "value": 10,
        "label": "10 Free Spins",
        "copy": "10 free spins — a small welcome back whenever you are ready",
        "terms": "Free spins valid on selected games. Winnings subject to wagering. Valid for 21 days.",
        "expiry_days": 21,
        "offer_band": "free_spins_small",
        "game_label": _DEFAULT_FREE_SPINS_GAME,
    },
}

# All cohorts the classifier can produce — used for validation.
KNOWN_COHORTS: frozenset[str] = frozenset(_COHORT_DEFAULTS)


class UnknownCohortError(ValueError):
    """Raised when *cohort* is not in the supported offer matrix."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def select_offer(cohort: str, player: "Player | None" = None) -> Offer:
    """Return the deterministic Offer for *cohort*.

    Parameters
    ----------
    cohort:
        One of the six classifier cohort strings.
    player:
        Optional Player instance.  When supplied, ``favorite_game_label`` is
        used for ``free_spins`` offers instead of the generic default.

    Raises
    ------
    UnknownCohortError
        If *cohort* is not in the supported matrix.
    """
    if cohort not in _COHORT_DEFAULTS:
        raise UnknownCohortError(
            f"Cohort {cohort!r} has no offer rule. "
            f"Expected one of: {sorted(KNOWN_COHORTS)}"
        )

    defaults = _COHORT_DEFAULTS[cohort].copy()

    # Personalise free_spins game label from player profile when available.
    if defaults["type"] == "free_spins" and player is not None:
        fav = player.favorite_game_label
        if fav:
            defaults["game_label"] = fav

    return Offer(cohort=cohort, **defaults)

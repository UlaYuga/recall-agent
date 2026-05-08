"""Tests for app.agent.offers — no LLM, no DB, no network calls."""
from __future__ import annotations

import pytest

from app.agent.offers import (
    KNOWN_COHORTS,
    Offer,
    UnknownCohortError,
    select_offer,
)
from app.models import Player

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ALL_COHORTS = sorted(KNOWN_COHORTS)


def _player(**kwargs) -> Player:
    defaults = dict(
        player_id="p_test",
        external_id="ext_test",
        first_name="Test",
        currency="EUR",
        ltv_segment="mid",
    )
    defaults.update(kwargs)
    return Player(**defaults)


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------


def test_select_offer_returns_offer_instance():
    offer = select_offer("casual_dormant")
    assert isinstance(offer, Offer)


# ---------------------------------------------------------------------------
# All six cohorts produce valid offers
# ---------------------------------------------------------------------------


class TestAllCohorts:
    def test_vip_at_risk(self):
        offer = select_offer("vip_at_risk")
        assert offer.type == "deposit_match"
        assert offer.value == 100
        assert offer.offer_band == "deposit_match_high"
        assert offer.expiry_days == 7
        assert offer.cohort == "vip_at_risk"

    def test_high_value_dormant(self):
        offer = select_offer("high_value_dormant")
        assert offer.type == "cashback"
        assert offer.value == 15
        assert offer.offer_band == "cashback"
        assert offer.expiry_days == 10
        assert offer.cohort == "high_value_dormant"

    def test_lapsed_loyal(self):
        offer = select_offer("lapsed_loyal")
        assert offer.type == "free_spins"
        assert offer.value == 50
        assert offer.offer_band == "free_spins_mid"
        assert offer.expiry_days == 14
        assert offer.cohort == "lapsed_loyal"

    def test_post_event(self):
        offer = select_offer("post_event")
        assert offer.type == "free_bet"
        assert offer.value == 10
        assert offer.offer_band == "free_bet"
        assert offer.expiry_days == 7
        assert offer.cohort == "post_event"

    def test_first_deposit_no_return(self):
        offer = select_offer("first_deposit_no_return")
        assert offer.type == "free_spins"
        assert offer.value == 20
        assert offer.offer_band == "free_spins_small"
        assert offer.expiry_days == 14
        assert offer.cohort == "first_deposit_no_return"

    def test_casual_dormant(self):
        offer = select_offer("casual_dormant")
        assert offer.type == "free_spins"
        assert offer.value == 10
        assert offer.offer_band == "free_spins_small"
        assert offer.expiry_days == 21
        assert offer.cohort == "casual_dormant"


# ---------------------------------------------------------------------------
# Required fields present on every offer
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cohort", _ALL_COHORTS)
def test_offer_has_required_fields(cohort: str):
    offer = select_offer(cohort)
    assert offer.label, f"label missing for {cohort}"
    assert offer.copy, f"copy missing for {cohort}"
    assert offer.terms, f"terms missing for {cohort}"
    assert offer.expiry_days > 0, f"expiry_days must be positive for {cohort}"
    assert offer.offer_band, f"offer_band missing for {cohort}"
    assert offer.cohort == cohort


# ---------------------------------------------------------------------------
# Deterministic output — identical inputs produce identical offers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cohort", _ALL_COHORTS)
def test_offers_are_deterministic(cohort: str):
    assert select_offer(cohort) == select_offer(cohort)


def test_deterministic_with_player():
    player = _player(favorite_game_label="neon_spins")
    assert select_offer("casual_dormant", player) == select_offer("casual_dormant", player)


# ---------------------------------------------------------------------------
# Unknown cohort raises
# ---------------------------------------------------------------------------


def test_unknown_cohort_raises():
    with pytest.raises(UnknownCohortError, match="long_dormant"):
        select_offer("long_dormant")


def test_empty_cohort_raises():
    with pytest.raises(UnknownCohortError):
        select_offer("")


def test_unknown_cohort_message_lists_valid_cohorts():
    with pytest.raises(UnknownCohortError, match="casual_dormant"):
        select_offer("bad_cohort")


# ---------------------------------------------------------------------------
# Player profile personalisation
# ---------------------------------------------------------------------------


def test_free_spins_uses_player_favorite_game_label():
    player = _player(favorite_game_label="neon_spins")
    offer = select_offer("casual_dormant", player)
    assert offer.game_label == "neon_spins"


def test_free_spins_falls_back_to_default_when_no_favorite():
    player = _player(favorite_game_label=None)
    offer = select_offer("casual_dormant", player)
    assert offer.game_label is not None  # default applied


def test_deposit_match_game_label_is_none():
    offer = select_offer("vip_at_risk")
    assert offer.game_label is None


def test_cashback_game_label_is_none():
    offer = select_offer("high_value_dormant")
    assert offer.game_label is None


def test_free_bet_game_label_is_none():
    offer = select_offer("post_event")
    assert offer.game_label is None


def test_player_favorite_not_used_for_non_free_spins():
    player = _player(favorite_game_label="neon_spins")
    offer = select_offer("vip_at_risk", player)
    assert offer.game_label is None  # deposit_match, game label n/a


# ---------------------------------------------------------------------------
# Offer band membership
# ---------------------------------------------------------------------------


from app.agent.offers import OFFER_BANDS  # noqa: E402


@pytest.mark.parametrize("cohort", _ALL_COHORTS)
def test_offer_band_is_valid(cohort: str):
    offer = select_offer(cohort)
    assert offer.offer_band in OFFER_BANDS, (
        f"{cohort} produced band {offer.offer_band!r} not in OFFER_BANDS"
    )


# ---------------------------------------------------------------------------
# Immutability (frozen dataclass)
# ---------------------------------------------------------------------------


def test_offer_is_immutable():
    offer = select_offer("casual_dormant")
    with pytest.raises((AttributeError, TypeError)):
        offer.value = 999  # type: ignore[misc]

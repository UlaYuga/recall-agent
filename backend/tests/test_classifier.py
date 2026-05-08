"""Deterministic classifier tests.

All tests pass an explicit `now` so results are independent of wall-clock time.
Cohort expectations are derived from the B-01 seed player profiles.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.agent.classifier import ClassificationResult, classify_player
from app.models import Player
from seeds.seed import load_players

# Reference point consistent with the seed player timestamps
NOW = datetime(2026, 5, 8, 12, 0, 0, tzinfo=timezone.utc)

# Expected cohort for each B-01 seed player (keyed by player_id)
EXPECTED_COHORTS: dict[str, str] = {
    "p_001": "high_value_dormant",   # Lucas  — high amount, 29 days inactive
    "p_002": "casual_dormant",       # Mariana — low amount, 39 days
    "p_003": "post_event",           # Thabo  — sportsbook, 18 days
    "p_004": "lapsed_loyal",         # Andrei — 29 deposits, 87 days
    "p_005": "first_deposit_no_return",  # James — count == 1
    "p_006": "casual_dormant",       # Sofia  — low amount, 52 days
    "p_007": "vip_at_risk",          # Ingrid — ltv=vip, 11 days
}


@pytest.fixture(scope="module")
def seed_results() -> dict[str, ClassificationResult]:
    players = load_players()
    return {p.player_id: classify_player(p, now=NOW) for p in players}


# ── Cohort correctness ──────────────────────────────────────────────────────

def test_all_cohorts_correct(seed_results: dict[str, ClassificationResult]) -> None:
    for pid, expected in EXPECTED_COHORTS.items():
        got = seed_results[pid].cohort
        assert got == expected, f"{pid}: expected {expected!r}, got {got!r}"


@pytest.mark.parametrize("player_id,cohort", EXPECTED_COHORTS.items())
def test_individual_cohort(
    seed_results: dict[str, ClassificationResult], player_id: str, cohort: str
) -> None:
    assert seed_results[player_id].cohort == cohort


# ── Result structure ────────────────────────────────────────────────────────

def test_result_is_classification_result(seed_results: dict[str, ClassificationResult]) -> None:
    for r in seed_results.values():
        assert isinstance(r, ClassificationResult)
        assert isinstance(r.cohort, str)
        assert isinstance(r.risk_score, int)
        assert isinstance(r.reasoning, list)


def test_all_risk_scores_in_range(seed_results: dict[str, ClassificationResult]) -> None:
    for pid, r in seed_results.items():
        assert 0 <= r.risk_score <= 100, f"{pid}: risk_score {r.risk_score} out of range"


def test_all_reasoning_non_empty(seed_results: dict[str, ClassificationResult]) -> None:
    for pid, r in seed_results.items():
        assert r.reasoning, f"{pid}: reasoning list is empty"
        assert all(isinstance(s, str) and s for s in r.reasoning)


# ── Determinism ─────────────────────────────────────────────────────────────

def test_now_injection_makes_result_deterministic() -> None:
    player = Player(
        player_id="det-001",
        external_id="det-001",
        first_name="Det",
        currency="NOK",
        ltv_segment="vip",
        total_deposits_count=37,
        total_deposits_amount=52200.0,
        last_login_at=NOW - timedelta(days=12),
    )
    r1 = classify_player(player, now=NOW)
    r2 = classify_player(player, now=NOW)
    assert r1.cohort == r2.cohort == "vip_at_risk"
    assert r1.risk_score == r2.risk_score


# ── Rule boundary checks ────────────────────────────────────────────────────

def test_first_deposit_trumps_vip() -> None:
    """A VIP player with only 1 deposit gets first_deposit_no_return."""
    player = Player(
        player_id="b-001",
        external_id="b-001",
        first_name="B",
        currency="USD",
        ltv_segment="vip",
        total_deposits_count=1,
        total_deposits_amount=200.0,
        last_login_at=NOW - timedelta(days=10),
        last_deposit_at=NOW - timedelta(days=10),
    )
    assert classify_player(player, now=NOW).cohort == "first_deposit_no_return"


def test_vip_trumps_sportsbook() -> None:
    """A VIP sportsbook player gets vip_at_risk, not post_event."""
    player = Player(
        player_id="b-002",
        external_id="b-002",
        first_name="B",
        currency="USD",
        ltv_segment="vip",
        favorite_vertical="sportsbook",
        total_deposits_count=5,
        total_deposits_amount=3000.0,
        last_login_at=NOW - timedelta(days=8),
    )
    assert classify_player(player, now=NOW).cohort == "vip_at_risk"


def test_sportsbook_over_30_days_is_not_post_event() -> None:
    """Sportsbook player inactive > 30 days falls through to the next rule."""
    player = Player(
        player_id="b-003",
        external_id="b-003",
        first_name="B",
        currency="USD",
        ltv_segment="mid",
        favorite_vertical="sportsbook",
        total_deposits_count=8,
        total_deposits_amount=400.0,
        last_login_at=NOW - timedelta(days=35),
        last_deposit_at=NOW - timedelta(days=35),
    )
    result = classify_player(player, now=NOW)
    assert result.cohort != "post_event"

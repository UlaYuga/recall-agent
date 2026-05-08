from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.models import Player

# ── LTV bonus points added to risk score ──────────────────────────────────
_LTV_BONUS: dict[str, int] = {"vip": 20, "high": 12, "mid": 6, "low": 0}

# ── Per-cohort weight reflects urgency / business value at risk ───────────
_COHORT_WEIGHT: dict[str, int] = {
    "vip_at_risk": 25,
    "high_value_dormant": 20,
    "lapsed_loyal": 18,
    "post_event": 15,
    "first_deposit_no_return": 12,
    "casual_dormant": 8,
}


@dataclass
class ClassificationResult:
    cohort: str
    risk_score: int          # 0–100
    reasoning: list[str] = field(default_factory=list)


def _days_since(dt: datetime | None, now: datetime) -> int:
    if dt is None:
        return 0
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0, (now - dt).days)


def _risk(cohort: str, days_login: int, ltv: str) -> int:
    raw = min(days_login * 2, 50) + _LTV_BONUS.get(ltv, 0) + _COHORT_WEIGHT.get(cohort, 5)
    return min(100, max(0, raw))


def classify_player(player: Player, now: datetime | None = None) -> ClassificationResult:
    """Return a deterministic ClassificationResult for *player*.

    Pass an explicit *now* to make results reproducible in tests.
    Defaults to current UTC time when omitted.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    days_login = _days_since(player.last_login_at, now)
    days_deposit = _days_since(player.last_deposit_at, now)
    ltv = player.ltv_segment or "low"

    # Rule 1 — first deposit, never returned
    if player.total_deposits_count == 1:
        cohort = "first_deposit_no_return"
        return ClassificationResult(
            cohort=cohort,
            risk_score=_risk(cohort, days_login, ltv),
            reasoning=[
                f"Single deposit of {player.total_deposits_amount} {player.currency}.",
                f"Inactive {days_login} days since last login.",
            ],
        )

    # Rule 2 — VIP showing any inactivity
    if ltv == "vip" and days_login >= 7:
        cohort = "vip_at_risk"
        return ClassificationResult(
            cohort=cohort,
            risk_score=_risk(cohort, days_login, ltv),
            reasoning=[
                f"VIP segment; {days_login} days since last login.",
                f"{player.total_deposits_count} lifetime deposits, "
                f"{player.total_deposits_amount} {player.currency} total.",
            ],
        )

    # Rule 3 — sportsbook player with recent post-event drop-off (< 30 days)
    if player.favorite_vertical == "sportsbook" and days_login < 30:
        cohort = "post_event"
        return ClassificationResult(
            cohort=cohort,
            risk_score=_risk(cohort, days_login, ltv),
            reasoning=[
                f"Sportsbook primary ({player.favorite_game_category}); "
                f"{days_login} days since last login.",
                "Post-event churn pattern: short inactivity after match activity.",
            ],
        )

    # Rule 4 — high cumulative value, deposit gap ≥ 14 days
    if player.total_deposits_amount >= 5000 and days_deposit >= 14:
        cohort = "high_value_dormant"
        return ClassificationResult(
            cohort=cohort,
            risk_score=_risk(cohort, days_login, ltv),
            reasoning=[
                f"High-value: {player.total_deposits_amount} {player.currency} "
                f"across {player.total_deposits_count} deposits.",
                f"Last deposit {days_deposit} days ago; login gap {days_login} days.",
            ],
        )

    # Rule 5 — long-tenure player with extended inactivity
    if player.total_deposits_count >= 20 and days_login >= 60:
        cohort = "lapsed_loyal"
        return ClassificationResult(
            cohort=cohort,
            risk_score=_risk(cohort, days_login, ltv),
            reasoning=[
                f"Long-tenure: {player.total_deposits_count} lifetime deposits.",
                f"Extended inactivity: {days_login} days since last login.",
            ],
        )

    # Default — casual dormant
    cohort = "casual_dormant"
    return ClassificationResult(
        cohort=cohort,
        risk_score=_risk(cohort, days_login, ltv),
        reasoning=[
            f"Inactive {days_login} days; no high-value, VIP, or sportsbook signal.",
            f"{player.total_deposits_count} deposits, "
            f"{player.total_deposits_amount} {player.currency} total.",
        ],
    )

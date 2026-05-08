from datetime import datetime, timezone

from app.models import Player


def _days_since(dt: datetime | None) -> int:
    if dt is None:
        return 0
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt).days


def classify_player(player: Player) -> str:
    days_inactive = _days_since(player.last_login_at)
    if player.total_deposits_amount >= 1000 and days_inactive >= 14:
        return "high_value_dormant"
    if days_inactive >= 21:
        return "long_dormant"
    if days_inactive >= 7:
        return "warm_dormant"
    return "not_eligible"

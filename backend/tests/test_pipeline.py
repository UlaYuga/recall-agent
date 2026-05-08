from datetime import datetime, timedelta, timezone

from app.agent.classifier import classify_player
from app.models import Player

_NOW = datetime(2026, 5, 8, 12, 0, 0, tzinfo=timezone.utc)


def test_classifies_high_value_dormant_player() -> None:
    player = Player(
        player_id="test-hvd",
        external_id="test-hvd",
        first_name="Test",
        country="BR",
        currency="BRL",
        total_deposits_count=10,
        total_deposits_amount=6000.0,
        last_login_at=_NOW - timedelta(days=20),
        last_deposit_at=_NOW - timedelta(days=20),
    )
    assert classify_player(player, now=_NOW).cohort == "high_value_dormant"

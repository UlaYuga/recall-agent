from datetime import datetime, timedelta, timezone

from app.agent.classifier import classify_player
from app.models import Player


def test_classifies_high_value_dormant_player() -> None:
    player = Player(
        player_id="test-001",
        external_id="test-001",
        first_name="Test",
        country="GB",
        currency="GBP",
        total_deposits_amount=1200.0,
        last_login_at=datetime.now(timezone.utc) - timedelta(days=14),
    )

    assert classify_player(player) == "high_value_dormant"

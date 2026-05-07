from app.agent.classifier import classify_player
from app.models import Player


def test_classifies_high_value_dormant_player() -> None:
    player = Player(
        external_id="test-001",
        name="Test",
        country="UK",
        currency="GBP",
        days_inactive=14,
        total_deposits_amount=1200,
    )

    assert classify_player(player) == "high_value_dormant"


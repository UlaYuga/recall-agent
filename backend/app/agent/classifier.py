from app.models import Player


def classify_player(player: Player) -> str:
    if player.total_deposits_amount >= 1000 and player.days_inactive >= 14:
        return "high_value_dormant"
    if player.days_inactive >= 21:
        return "long_dormant"
    if player.days_inactive >= 7:
        return "warm_dormant"
    return "not_eligible"


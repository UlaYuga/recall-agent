from app.models import Player


def can_send_channel(player: Player, channel: str) -> bool:
    if not player.marketing_consent:
        return False
    if channel == "telegram":
        return bool(player.telegram_chat_id)
    return True


import json
from typing import Optional

from app.models import Campaign, Player


def check_generation_consent(player: Player) -> bool:
    """Returns True if the player has the required generation consent.

    Required: data_processing AND video_personalization.
    If missing -> campaign blocked before video pipeline:
        status = blocked_generation_consent (or ineligibility flag).
    """
    return bool(player.consent_data_processing and player.consent_video_personalization)


def generation_block_reason(player: Player) -> Optional[str]:
    if check_generation_consent(player):
        return None
    missing = []
    if not player.consent_data_processing:
        missing.append("data_processing")
    if not player.consent_video_personalization:
        missing.append("video_personalization")
    return f"missing_generation_consent: {', '.join(missing)}"


def check_delivery_consent(player: Player) -> bool:
    """Returns True if the player has the base delivery consent.

    Required: marketing_communications.
    Channel-specific consent is checked per-adapter.
    """
    return bool(player.consent_marketing_communications)


def get_available_channels(player: Player) -> list[str]:
    """Return all delivery channels available for this player.

    Evaluates marketing_communications + channel-specific consent + identifier presence.
    Returns channel names in player's preferred order (intersection with available).
    """
    if not check_delivery_consent(player):
        return []

    channels: list[str] = []

    if player.telegram_chat_id:
        channels.append("telegram")

    if player.email and player.consent_marketing_email:
        channels.append("email")

    if player.phone_e164 and player.consent_marketing_sms:
        channels.append("sms")

    if player.phone_e164 and player.consent_whatsapp_business:
        channels.append("whatsapp")

    if player.push_token and player.consent_push_notifications:
        channels.append("push")

    preferred = _parse_preferred_channels(player)
    if preferred:
        channels = [c for c in preferred if c in channels]

    return channels


def can_send_channel(player: Player, channel: str) -> bool:
    """Check if a specific channel is available for the player."""
    if not check_delivery_consent(player):
        return False
    if channel == "telegram":
        return bool(player.telegram_chat_id)
    if channel == "email":
        return bool(player.email and player.consent_marketing_email)
    if channel == "sms":
        return bool(player.phone_e164 and player.consent_marketing_sms)
    if channel == "whatsapp":
        return bool(player.phone_e164 and player.consent_whatsapp_business)
    if channel == "push":
        return bool(player.push_token and player.consent_push_notifications)
    return False


def can_send_any_channel(player: Player) -> bool:
    """Returns True if at least one channel is available."""
    return len(get_available_channels(player)) > 0


def select_best_channel(
    player: Player, campaign: Campaign | None = None
) -> Optional[str]:
    """Pick the best delivery channel for the player.

    Tries preferred_channels first, then falls back to first available.
    Returns None if no channel is available.
    """
    available = get_available_channels(player)
    if not available:
        return None
    return available[0]


def block_reason(player: Player, channel: str) -> Optional[str]:
    """Return the reason a channel is blocked, or None if it is available."""
    if not check_delivery_consent(player):
        return "blocked_no_marketing_consent"
    if can_send_channel(player, channel):
        return None
    if channel == "telegram":
        return "blocked_no_telegram_chat_id"
    if channel == "email":
        if not player.email:
            return "blocked_no_email_identifier"
        if not player.consent_marketing_email:
            return "blocked_no_email_consent"
    if channel == "sms":
        if not player.phone_e164:
            return "blocked_no_phone_identifier"
        if not player.consent_marketing_sms:
            return "blocked_no_sms_consent"
    if channel == "whatsapp":
        if not player.phone_e164:
            return "blocked_no_phone_identifier"
        if not player.consent_whatsapp_business:
            return "blocked_no_whatsapp_consent"
    if channel == "push":
        if not player.push_token:
            return "blocked_no_push_token"
        if not player.consent_push_notifications:
            return "blocked_no_push_consent"
    return f"blocked_unknown_channel_{channel}"


def build_delivery_block_reason(player: Player) -> Optional[str]:
    """Return an aggregate delivery-block reason or None.

    Used when video is ready but no delivery channel is reachable.
    """
    if not check_delivery_consent(player):
        return "blocked_no_marketing_consent"
    available = get_available_channels(player)
    if not available:
        return "blocked_no_reachable_channel"
    return None


def _parse_preferred_channels(player: Player) -> list[str]:
    if not player.preferred_channels:
        return []
    try:
        parsed = json.loads(player.preferred_channels)
        if isinstance(parsed, list):
            return [str(c) for c in parsed]
    except (json.JSONDecodeError, TypeError):
        pass
    return []

from typing import Optional

from aiogram import Bot

from app.config import settings
from app.delivery.adapters import DeliveryAdapter, DeliveryResult, DeliveryStatus
from app.delivery.eligibility import can_send_channel
from app.models import Campaign, Player, VideoAsset


class TelegramAdapter(DeliveryAdapter):
    """Real Telegram delivery via aiogram Bot.

    MVP behavior (TECH_SPEC §6.3):
      - sendPhoto(poster) + InlineKeyboardButton "Watch video" → landing.
      - Optional sendVideo if under 50MB.
      - Dependencies: Bot instance (injectable for testing).
    """

    def __init__(self, bot: Optional[Bot] = None):
        self._bot = bot

    def _get_bot(self) -> Bot:
        if self._bot is not None:
            return self._bot
        token = settings.telegram_bot_token
        if not token or token == "replace_me":
            raise ValueError(
                "TELEGRAM_BOT_TOKEN is not set or still has the placeholder value"
            )
        return Bot(token=token)

    def _landing_url(self, campaign_id: str) -> str:
        base = settings.base_url.rstrip("/")
        return f"{base}/r/{campaign_id}"

    def can_send(self, player: Player, campaign: Campaign) -> bool:
        return can_send_channel(player, "telegram")

    async def send(
        self,
        player: Player,
        campaign: Campaign,
        asset: Optional[VideoAsset] = None,
    ) -> DeliveryResult:
        if not self.can_send(player, campaign):
            return DeliveryResult(
                campaign_id=campaign.campaign_id,
                channel="telegram",
                status="skipped",
                reason="blocked_no_telegram_chat_id",
            )

        chat_id = int(player.telegram_chat_id)  # type: ignore[arg-type]
        poster_url = asset.poster_url if asset else None
        landing_url = self._landing_url(campaign.campaign_id)

        caption = ""
        offer_raw = campaign.offer_json
        if offer_raw:
            import json as _json

            try:
                offer = _json.loads(offer_raw)
                offer_text = offer.get("description", offer.get("type", ""))
                caption = f"{offer_text}\n\nWatch your personal video: {landing_url}"
            except (_json.JSONDecodeError, TypeError):
                caption = f"Watch your personal video: {landing_url}"
        else:
            caption = f"Watch your personal video: {landing_url}"

        bot = self._get_bot()
        message_id: Optional[str] = None

        if poster_url:
            sent = await bot.send_photo(
                chat_id=chat_id,
                photo=poster_url,
                caption=caption,
            )
            message_id = str(sent.message_id)
        else:
            sent = await bot.send_message(
                chat_id=chat_id,
                text=caption,
            )
            message_id = str(sent.message_id)

        return DeliveryResult(
            campaign_id=campaign.campaign_id,
            channel="telegram",
            status="sent",
            message_id=message_id,
            recipient=str(chat_id),
        )

    async def get_status(self, campaign_id: str) -> DeliveryStatus:
        return DeliveryStatus(
            campaign_id=campaign_id,
            channel="telegram",
            status="delivered",
        )

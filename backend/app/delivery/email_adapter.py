from typing import Optional

from app.config import settings
from app.delivery.adapters import DeliveryAdapter, DeliveryResult, DeliveryStatus
from app.delivery.eligibility import can_send_channel
from app.models import Campaign, Player, VideoAsset


class EmailPosterAdapter(DeliveryAdapter):
    """Stub email adapter for MVP.

    TECH_SPEC §6.3:
      - Dashboard shows email preview: subject + poster + CTA + landing URL.
      - Status: 'prepared' — not actually sent.
      - "Mark as sent" button is a dashboard UX concern (T-24 / T-29).
    """

    def _landing_url(self, campaign_id: str) -> str:
        base = settings.base_url.rstrip("/")
        return f"{base}/r/{campaign_id}"

    def _subject(self, player: Player) -> str:
        return f"{player.first_name}, your personal reward is waiting"

    def can_send(self, player: Player, campaign: Campaign) -> bool:
        return can_send_channel(player, "email")

    async def send(
        self,
        player: Player,
        campaign: Campaign,
        asset: Optional[VideoAsset] = None,
    ) -> DeliveryResult:
        if not self.can_send(player, campaign):
            return DeliveryResult(
                campaign_id=campaign.campaign_id,
                channel="email",
                status="skipped",
                reason="blocked_email_unavailable",
            )

        return DeliveryResult(
            campaign_id=campaign.campaign_id,
            channel="email",
            status="prepared",
            recipient=player.email,
            message_id=None,
        )

    async def get_status(self, campaign_id: str) -> DeliveryStatus:
        """Returns the last known delivery status (stub)."""
        return DeliveryStatus(
            campaign_id=campaign_id,
            channel="email",
            status="prepared",
        )

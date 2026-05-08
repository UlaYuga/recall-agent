from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable

from app.models import Campaign, Player, VideoAsset


@dataclass
class DeliveryResult:
    campaign_id: str
    channel: str
    status: str  # sent | prepared | skipped | failed
    reason: Optional[str] = None
    message_id: Optional[str] = None
    recipient: Optional[str] = None


@dataclass
class DeliveryStatus:
    campaign_id: str
    channel: str
    status: str
    recipient: Optional[str] = None
    sent_at: Optional[str] = None
    delivered_at: Optional[str] = None
    clicked_at: Optional[str] = None
    failure_reason: Optional[str] = None


@runtime_checkable
class DeliveryAdapter(Protocol):
    """Protocol that all delivery channel adapters must implement.

    TECH_SPEC §6.1: each adapter exposes can_send, send, and get_status.
    Adapters are instantiated with optional dependencies (bot, config)
    and operate on Player, Campaign, and optional VideoAsset.
    """

    def can_send(self, player: Player, campaign: Campaign) -> bool: ...

    async def send(
        self,
        player: Player,
        campaign: Campaign,
        asset: Optional[VideoAsset] = None,
    ) -> DeliveryResult: ...

    async def get_status(self, campaign_id: str) -> DeliveryStatus: ...

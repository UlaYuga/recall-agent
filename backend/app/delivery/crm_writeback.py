from datetime import datetime, timezone
from typing import Optional


class CrmWritebackAdapter:
    """Mock CRM write-back adapter.

    TECH_SPEC §6.3:
      - Writes status to local SQLite DB (or returns structured result).
      - Production roadmap: real CRM vendor integration.
    """

    @staticmethod
    def write_status(
        campaign_id: str,
        status: str,
        channel: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> dict:
        payload: dict = {
            "campaign_id": campaign_id,
            "status": status,
            "written_at": datetime.now(timezone.utc).isoformat(),
        }
        if channel:
            payload["channel"] = channel
        if reason:
            payload["reason"] = reason
        return payload

    @staticmethod
    def write_delivery(
        campaign_id: str,
        channel: str,
        delivery_status: str,
        recipient: Optional[str] = None,
    ) -> dict:
        return {
            "campaign_id": campaign_id,
            "channel": channel,
            "status": delivery_status,
            "recipient": recipient,
            "written_at": datetime.now(timezone.utc).isoformat(),
        }

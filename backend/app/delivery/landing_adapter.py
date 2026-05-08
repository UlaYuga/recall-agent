from app.config import settings


class LandingTrackingAdapter:
    """Generate landing URLs and scope for tracking events.

    TECH_SPEC §6.3: real tracking events on the landing page.
    This adapter provides URL generation; actual tracking is wired
    through the backend /track endpoints (T-25 scope).
    """

    @staticmethod
    def link_for(campaign_id: str) -> str:
        base = settings.base_url.rstrip("/")
        return f"{base}/r/{campaign_id}"

    @staticmethod
    def tracking_pixel_url(campaign_id: str, event_type: str) -> str:
        """Return the backend tracking webhook URL for a given event."""
        base = settings.base_url.rstrip("/")
        return f"{base}/track/{event_type}?campaign_id={campaign_id}"

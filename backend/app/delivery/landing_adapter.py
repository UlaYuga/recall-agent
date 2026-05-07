class LandingTrackingAdapter:
    def link_for(self, campaign_id: int, base_url: str) -> str:
        return f"{base_url.rstrip('/')}/r/{campaign_id}"


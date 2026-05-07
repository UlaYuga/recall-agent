class EmailPosterAdapter:
    def send(self, campaign_id: int, asset_url: str) -> str:
        return f"email-preview:queued:{campaign_id}:{asset_url}"


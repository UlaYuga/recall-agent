class TelegramAdapter:
    def send(self, campaign_id: int, asset_url: str) -> str:
        return f"telegram:queued:{campaign_id}:{asset_url}"


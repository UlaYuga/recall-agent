from typing import Protocol


class DeliveryAdapter(Protocol):
    def send(self, campaign_id: int, asset_url: str) -> str:
        ...


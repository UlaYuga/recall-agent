class CrmWritebackAdapter:
    def write_status(self, campaign_id: int, status: str) -> dict[str, int | str]:
        return {"campaign_id": campaign_id, "status": status}


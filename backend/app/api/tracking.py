from fastapi import APIRouter

router = APIRouter()


@router.post("/{campaign_id}/{event_type}")
def track(campaign_id: int, event_type: str) -> dict[str, int | str]:
    return {"campaign_id": campaign_id, "event_type": event_type, "status": "recorded"}


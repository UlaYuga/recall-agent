from fastapi import APIRouter

router = APIRouter()


@router.post("")
def ingest_event() -> dict[str, str]:
    return {"status": "accepted"}


from fastapi import APIRouter

router = APIRouter()


@router.post("/send")
def send() -> dict[str, str]:
    return {"status": "queued"}


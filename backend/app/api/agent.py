from fastapi import APIRouter

router = APIRouter()


@router.post("/scan")
def scan() -> dict[str, str]:
    return {"status": "queued"}


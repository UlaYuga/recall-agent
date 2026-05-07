from fastapi import APIRouter

router = APIRouter()


@router.get("/queue")
def queue() -> list[dict[str, str]]:
    return []


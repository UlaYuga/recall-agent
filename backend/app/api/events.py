from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from seeds.seed import seed_database

router = APIRouter()


@router.post("")
def ingest_event() -> dict[str, str]:
    return {"status": "accepted"}


@router.post("/seed")
def seed(session: Annotated[Session, Depends(get_session)]) -> dict[str, int]:
    return seed_database(session)

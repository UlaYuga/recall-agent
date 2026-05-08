from collections.abc import Generator

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

engine = create_engine(settings.database_url, echo=False)


def init_db(bind: Engine | None = None) -> None:
    SQLModel.metadata.create_all(bind or engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


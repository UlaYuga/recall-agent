import pytest
from sqlalchemy import inspect
from sqlmodel import Session, SQLModel, create_engine

from app import db


@pytest.fixture()
def mem_engine():
    import app.models  # noqa: F401 — registers tables in SQLModel.metadata
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    yield eng
    eng.dispose()


def test_init_db_creates_tables(mem_engine) -> None:
    db.init_db(bind=mem_engine)
    tables = inspect(mem_engine).get_table_names()
    assert "player" in tables
    assert "campaign" in tables
    assert "trackingevent" in tables


def test_get_session_yields_session(monkeypatch, mem_engine) -> None:
    SQLModel.metadata.create_all(mem_engine)
    monkeypatch.setattr(db, "engine", mem_engine)
    gen = db.get_session()
    session = next(gen)
    assert isinstance(session, Session)
    gen.close()

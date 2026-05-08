import json

import pytest
from sqlmodel import Session, SQLModel, create_engine

from seeds.seed import load_events, load_players, seed_database


@pytest.fixture()
def mem_session():
    import app.models  # noqa: F401 — registers all tables
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(eng)
    with Session(eng) as session:
        yield session
    eng.dispose()


def test_load_players_returns_7() -> None:
    players = load_players()
    assert len(players) == 7


def test_load_events_returns_96() -> None:
    events = load_events()
    assert len(events) == 96


def test_first_player_fields() -> None:
    players = load_players()
    p = players[0]
    assert p.player_id == "p_001"
    assert p.first_name == "Lucas"
    assert p.telegram_chat_id == "mock_tg_001"
    assert p.consent_data_processing is True
    assert "high_value_dormant" in json.loads(p.tags or "[]")


def test_first_event_fields() -> None:
    events = load_events()
    e = events[0]
    assert e.event_id == "evt_0001"
    assert e.player_id == "p_001"
    assert json.loads(e.metadata_json or "{}")["source"] == "mock_event_bus_v1"


def test_seed_database_is_idempotent(mem_session: Session) -> None:
    counts1 = seed_database(mem_session)
    counts2 = seed_database(mem_session)
    assert counts2["players"] == 7
    assert counts2["events"] == 96
    assert counts1 == counts2

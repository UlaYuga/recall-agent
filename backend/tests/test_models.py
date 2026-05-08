import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect
from sqlmodel import Session, SQLModel, create_engine

from app.models import Event, Player


@pytest.fixture()
def mem_engine():
    import app.models  # noqa: F401 — registers all tables in SQLModel.metadata
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(eng)
    yield eng
    eng.dispose()


def test_all_required_tables_created(mem_engine) -> None:
    tables = set(inspect(mem_engine).get_table_names())
    required = {"player", "event", "campaign", "videoasset", "delivery", "tracking", "runwaytask"}
    assert required.issubset(tables)


def test_player_represents_b01_first_entry(mem_engine) -> None:
    """Player row round-trips the first B-01 seed player without lossy mapping."""
    player = Player(
        player_id="p_001",
        external_id="demo_op_4471",
        first_name="Lucas",
        preferred_language="en",
        market_language="pt-BR",
        country="BR",
        currency="BRL",
        registered_at=datetime(2025, 8, 12, 14, 23, 0, tzinfo=timezone.utc),
        last_login_at=datetime(2026, 4, 8, 19, 11, 0, tzinfo=timezone.utc),
        last_deposit_at=datetime(2026, 4, 5, 20, 44, 0, tzinfo=timezone.utc),
        total_deposits_count=14,
        total_deposits_amount=7100.0,
        ltv_segment="high",
        biggest_win_amount=3100.0,
        biggest_win_currency="BRL",
        biggest_win_at=datetime(2026, 3, 22, tzinfo=timezone.utc),
        tags=json.dumps(["high_value_dormant", "weekly_player", "telegram_subscribed"]),
        preferred_channels=json.dumps(["telegram", "email", "whatsapp", "push"]),
        external_crm_id="crm_9f2a",
        email="lucas.pereira.demo@example.com",
        phone_e164="+551100000001",
        telegram_chat_id="mock_tg_001",
        push_token="mock_push_token_001",
        consent_marketing_communications=True,
        consent_marketing_email=True,
        consent_marketing_sms=False,
        consent_whatsapp_business=True,
        consent_push_notifications=True,
        consent_video_personalization=True,
        consent_data_processing=True,
    )
    with Session(mem_engine) as session:
        session.add(player)
        session.commit()
        session.refresh(player)

    assert player.id is not None
    assert player.player_id == "p_001"
    assert player.first_name == "Lucas"
    assert player.total_deposits_count == 14
    assert player.consent_video_personalization is True
    assert json.loads(player.tags or "[]")[0] == "high_value_dormant"
    assert "telegram" in json.loads(player.preferred_channels or "[]")


def test_event_represents_b02_first_entry(mem_engine) -> None:
    """Event row round-trips the first B-02 seed event."""
    event = Event(
        event_id="evt_0001",
        player_id="p_001",
        event_type="login",
        event_at=datetime(2025, 8, 12, 15, 0, 0, tzinfo=timezone.utc),
        vertical="casino",
        game_category="slots",
        game_label="fruit_slots",
        amount=None,
        currency="BRL",
        metadata_json=json.dumps({"source": "mock_event_bus_v1"}),
    )
    with Session(mem_engine) as session:
        session.add(event)
        session.commit()
        session.refresh(event)

    assert event.id is not None
    assert event.event_id == "evt_0001"
    assert event.event_type == "login"
    assert json.loads(event.metadata_json or "{}")["source"] == "mock_event_bus_v1"


def test_event_metadata_json_roundtrip(mem_engine) -> None:
    """metadata_json survives a nested payload without SQLAlchemy choking."""
    payload = {"source": "mock_event_bus_v1", "tags": ["x", "y"], "nested": {"k": 42}}
    event = Event(
        event_id="evt_json_rt",
        player_id="p_001",
        event_type="bet_placed",
        event_at=datetime.now(timezone.utc),
        metadata_json=json.dumps(payload),
    )
    with Session(mem_engine) as session:
        session.add(event)
        session.commit()
        session.refresh(event)

    assert json.loads(event.metadata_json) == payload

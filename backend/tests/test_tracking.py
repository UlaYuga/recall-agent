"""Tests for /track endpoints: play, click, deposit."""
from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

import app.models  # noqa: F401
from app.db import get_session
from app.main import app
from app.models import Campaign, CampaignStatus, Delivery, Player, Tracking

_NOW = datetime(2026, 5, 8, 20, 0, 0, tzinfo=timezone.utc)


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture()
def engine():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    url = f"sqlite:///{tmp.name}"
    eng = create_engine(url, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(eng)
    yield eng
    eng.dispose()
    Path(tmp.name).unlink(missing_ok=True)


@pytest.fixture()
def session(engine):
    with Session(engine) as sess:
        yield sess


@pytest.fixture()
def client(engine):
    def override():
        with Session(engine) as sess:
            yield sess

    app.dependency_overrides[get_session] = override
    yield TestClient(app)
    app.dependency_overrides.pop(get_session, None)


def _player(**overrides) -> Player:
    defaults = {
        "player_id": "p_test",
        "external_id": "ext_test",
        "first_name": "Test",
        "country": "XX",
        "currency": "USD",
        "telegram_chat_id": "123456789",
        "email": "test@example.com",
        "consent_marketing_communications": True,
        "consent_marketing_email": True,
        "consent_video_personalization": True,
        "consent_data_processing": True,
    }
    defaults.update(overrides)
    return Player(**defaults)


def _campaign(**overrides) -> Campaign:
    defaults = {
        "campaign_id": "cmp_test",
        "player_id": "p_test",
        "cohort": "casual_dormant",
        "status": CampaignStatus.delivered,
        "risk_score": 45.0,
    }
    defaults.update(overrides)
    return Campaign(**defaults)


def _delivery(campaign_id: str = "cmp_test", channel: str = "telegram", status: str = "sent") -> Delivery:
    return Delivery(campaign_id=campaign_id, channel=channel, status=status)


def _seed(session: Session, with_delivery: bool = True):
    p = _player()
    session.add(p)
    c = _campaign()
    session.add(c)
    if with_delivery:
        d = _delivery()
        session.add(d)
    session.flush()
    session.commit()
    return p, c


def _tracking_count(session: Session, campaign_id: str) -> int:
    return len(session.exec(select(Tracking).where(Tracking.campaign_id == campaign_id)).all())


# ── Track Play ──────────────────────────────────────────────────────────────


class TestTrackPlay:
    def test_persists_tracking(self, session, client):
        _seed(session)
        r = client.post("/track/play", json={"campaign_id": "cmp_test"})
        assert r.status_code == 200
        assert r.json()["event_type"] == "video_play"
        assert r.json()["status"] == "recorded"
        assert _tracking_count(session, "cmp_test") == 1

    def test_optional_watched_seconds(self, session, client):
        _seed(session)
        r = client.post("/track/play", json={"campaign_id": "cmp_test", "watched_seconds": 32})
        assert r.status_code == 200
        assert r.json()["watched_seconds"] == 32

    def test_negative_watched_seconds_rejected(self, session, client):
        _seed(session)
        r = client.post("/track/play", json={"campaign_id": "cmp_test", "watched_seconds": -1})
        assert r.status_code == 422

    def test_missing_campaign_404(self, client):
        r = client.post("/track/play", json={"campaign_id": "nonexistent"})
        assert r.status_code == 404

    def test_missing_campaign_id_422(self, client):
        r = client.post("/track/play", json={})
        assert r.status_code == 422


# ── Track Click ─────────────────────────────────────────────────────────────


class TestTrackClick:
    def test_persists_tracking(self, session, client):
        _seed(session)
        r = client.post("/track/click", json={"campaign_id": "cmp_test"})
        assert r.status_code == 200
        assert r.json()["event_type"] == "cta_click"
        assert _tracking_count(session, "cmp_test") == 1

    def test_updates_delivery_clicked_at(self, session, client):
        _seed(session)
        r = client.post("/track/click", json={"campaign_id": "cmp_test"})
        assert r.status_code == 200

        session.expire_all()
        delivery = session.exec(
            select(Delivery).where(Delivery.campaign_id == "cmp_test")
        ).first()
        assert delivery is not None
        assert delivery.clicked_at is not None

    def test_click_without_delivery_still_works(self, session, client):
        _seed(session, with_delivery=False)
        r = client.post("/track/click", json={"campaign_id": "cmp_test"})
        assert r.status_code == 200
        assert _tracking_count(session, "cmp_test") == 1

    def test_optional_link_id(self, session, client):
        _seed(session)
        r = client.post("/track/click", json={"campaign_id": "cmp_test", "link_id": "cta_button_1"})
        assert r.status_code == 200
        assert r.json()["link_id"] == "cta_button_1"

    def test_missing_campaign_404(self, client):
        r = client.post("/track/click", json={"campaign_id": "nonexistent"})
        assert r.status_code == 404


# ── Track Deposit ───────────────────────────────────────────────────────────


class TestTrackDeposit:
    def test_persists_tracking(self, session, client):
        _seed(session)
        r = client.post(
            "/track/deposit",
            json={"campaign_id": "cmp_test", "amount": 50.0, "currency": "USD"},
        )
        assert r.status_code == 200
        assert r.json()["event_type"] == "deposit_submit"
        assert _tracking_count(session, "cmp_test") == 1

    def test_sets_campaign_converted(self, session, client):
        _seed(session)
        r = client.post(
            "/track/deposit",
            json={"campaign_id": "cmp_test", "amount": 75.0, "currency": "EUR"},
        )
        assert r.status_code == 200

        session.expire_all()
        c = session.exec(
            select(Campaign).where(Campaign.campaign_id == "cmp_test")
        ).first()
        assert c is not None
        assert c.status == CampaignStatus.converted
        assert c.updated_at is not None

    def test_calls_crm_writeback(self, session, client, monkeypatch):
        _seed(session)
        called = []

        def fake_write_status(campaign_id, status, channel=None, reason=None):
            called.append((campaign_id, status))
            return {}

        monkeypatch.setattr(
            "app.delivery.crm_writeback.CrmWritebackAdapter.write_status",
            fake_write_status,
        )

        client.post(
            "/track/deposit",
            json={"campaign_id": "cmp_test", "amount": 100.0, "currency": "USD"},
        )
        assert len(called) == 1
        assert called[0] == ("cmp_test", "converted")

    def test_zero_amount_rejected(self, session, client):
        _seed(session)
        r = client.post(
            "/track/deposit",
            json={"campaign_id": "cmp_test", "amount": 0, "currency": "USD"},
        )
        assert r.status_code == 422

    def test_negative_amount_rejected(self, session, client):
        _seed(session)
        r = client.post(
            "/track/deposit",
            json={"campaign_id": "cmp_test", "amount": -10, "currency": "USD"},
        )
        assert r.status_code == 422

    def test_short_currency_rejected(self, session, client):
        _seed(session)
        r = client.post(
            "/track/deposit",
            json={"campaign_id": "cmp_test", "amount": 50, "currency": "US"},
        )
        assert r.status_code == 422

    def test_missing_campaign_404(self, client):
        r = client.post(
            "/track/deposit",
            json={"campaign_id": "nonexistent", "amount": 50.0, "currency": "USD"},
        )
        assert r.status_code == 404

    def test_missing_required_fields_422(self, client):
        r = client.post("/track/deposit", json={"campaign_id": "cmp_test"})
        assert r.status_code == 422


# ── Tracking row attributes ─────────────────────────────────────────────────


class TestTrackingRow:
    def test_multiple_events_for_same_campaign(self, session, client):
        _seed(session)
        client.post("/track/play", json={"campaign_id": "cmp_test"})
        client.post("/track/click", json={"campaign_id": "cmp_test"})
        client.post(
            "/track/deposit",
            json={"campaign_id": "cmp_test", "amount": 25.0, "currency": "USD"},
        )
        assert _tracking_count(session, "cmp_test") == 3

    def test_tracking_rows_have_created_at(self, session, client):
        _seed(session)
        client.post("/track/play", json={"campaign_id": "cmp_test"})
        row = session.exec(
            select(Tracking).where(Tracking.campaign_id == "cmp_test")
        ).first()
        assert row is not None
        assert row.created_at is not None

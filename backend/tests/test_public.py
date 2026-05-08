"""Tests for GET /public/r/{campaign_id} — reactivation landing card."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db import get_session
from app.main import app
from app.models import Campaign, CampaignStatus, Player, VideoAsset


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(name="engine")
def engine_fixture():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(eng)
    yield eng


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Seed helpers ──────────────────────────────────────────────────────────────


def _player(**kw) -> Player:
    defaults = {
        "player_id": "p_pub",
        "external_id": "ext_pub",
        "first_name": "Lucas",
        "country": "BR",
        "currency": "BRL",
        "preferred_language": "en",
        "consent_marketing_communications": True,
        "consent_marketing_email": True,
        "consent_video_personalization": True,
        "consent_data_processing": True,
        "preferred_channels": json.dumps(["telegram", "email"]),
    }
    defaults.update(kw)
    return Player(**defaults)


def _campaign(**kw) -> Campaign:
    defaults = {
        "campaign_id": "cmp_pub",
        "player_id": "p_pub",
        "cohort": "high_value_dormant",
        "status": CampaignStatus.ready,
        "risk_score": 72.0,
    }
    defaults.update(kw)
    return Campaign(**defaults)


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_not_found(client: TestClient) -> None:
    r = client.get("/public/r/does_not_exist")
    assert r.status_code == 404


def test_found_no_video_asset(client: TestClient, session: Session) -> None:
    session.add(_player())
    session.add(_campaign())
    session.commit()

    r = client.get("/public/r/cmp_pub")
    assert r.status_code == 200
    data = r.json()
    assert data["campaign_id"] == "cmp_pub"
    assert data["first_name"] == "Lucas"
    assert data["cohort"] == "high_value_dormant"
    assert data["status"] == "ready"
    assert data["preferred_language"] == "en"
    assert data["currency"] == "BRL"
    assert data["video_url"] is None
    assert data["poster_url"] is None


def test_found_with_ready_video(client: TestClient, session: Session) -> None:
    session.add(_player())
    session.add(_campaign())
    asset = VideoAsset(
        campaign_id="cmp_pub",
        status="ready",
        video_url="https://cdn.example.com/cmp_pub/video.mp4",
        poster_url="https://cdn.example.com/cmp_pub/poster.jpg",
    )
    session.add(asset)
    session.commit()

    r = client.get("/public/r/cmp_pub")
    assert r.status_code == 200
    data = r.json()
    assert data["video_url"] == "https://cdn.example.com/cmp_pub/video.mp4"
    assert data["poster_url"] == "https://cdn.example.com/cmp_pub/poster.jpg"


def test_generating_video_url_not_exposed(client: TestClient, session: Session) -> None:
    """While the asset is still generating, video_url must be null."""
    session.add(_player())
    session.add(_campaign(status=CampaignStatus.generating))
    asset = VideoAsset(campaign_id="cmp_pub", status="generating")
    session.add(asset)
    session.commit()

    r = client.get("/public/r/cmp_pub")
    assert r.status_code == 200
    assert r.json()["video_url"] is None


def test_poster_exposed_before_video_ready(client: TestClient, session: Session) -> None:
    """poster_url is exposed as soon as it's set, even when status is generating."""
    session.add(_player())
    session.add(_campaign(status=CampaignStatus.generating))
    asset = VideoAsset(
        campaign_id="cmp_pub",
        status="generating",
        poster_url="https://cdn.example.com/cmp_pub/poster.jpg",
    )
    session.add(asset)
    session.commit()

    r = client.get("/public/r/cmp_pub")
    assert r.status_code == 200
    data = r.json()
    assert data["video_url"] is None
    assert data["poster_url"] == "https://cdn.example.com/cmp_pub/poster.jpg"


def test_offer_json_included(client: TestClient, session: Session) -> None:
    offer = json.dumps({"type": "free_spins", "label": "50 Free Spins", "value": 50,
                        "copy": "Play now", "terms": "T&C apply", "expiry_days": 7,
                        "offer_band": "mid", "game_label": None, "cohort": "high_value_dormant"})
    session.add(_player())
    session.add(_campaign(offer_json=offer))
    session.commit()

    r = client.get("/public/r/cmp_pub")
    assert r.status_code == 200
    assert r.json()["offer_json"] == offer


def test_player_sensitive_fields_not_exposed(client: TestClient, session: Session) -> None:
    """The response must NOT contain internal player/financial fields."""
    session.add(_player())
    session.add(_campaign())
    session.commit()

    r = client.get("/public/r/cmp_pub")
    assert r.status_code == 200
    data = r.json()
    assert "player_id" not in data
    assert "email" not in data
    assert "telegram_chat_id" not in data
    assert "total_deposits_amount" not in data

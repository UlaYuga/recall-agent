"""Tests for POST /agent/scan and GET /agent/decide/{player_id}.

All LLM calls are short-circuited; script_generator falls back to templates.
DB uses an in-memory SQLite via the conftest fixtures (session / client).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

import app.agent.script_generator as script_generator
from app.models import Campaign, CampaignStatus, Player

_NOW = datetime(2026, 5, 8, 12, 0, 0, tzinfo=timezone.utc)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _disable_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force script_generator to use the B-03 fallback (no network calls)."""
    monkeypatch.setattr(script_generator, "_make_client", lambda: None)


def _make_player(
    player_id: str = "p_test",
    *,
    first_name: str = "Test",
    country: str = "BR",
    currency: str = "BRL",
    total_deposits_count: int = 5,
    total_deposits_amount: float = 1_000.0,
    last_login_at: datetime | None = None,
    last_deposit_at: datetime | None = None,
) -> Player:
    return Player(
        player_id=player_id,
        external_id=player_id,
        first_name=first_name,
        country=country,
        currency=currency,
        total_deposits_count=total_deposits_count,
        total_deposits_amount=total_deposits_amount,
        last_login_at=last_login_at or _NOW - timedelta(days=30),
        last_deposit_at=last_deposit_at or _NOW - timedelta(days=30),
    )


# ── POST /agent/scan ──────────────────────────────────────────────────────────


class TestScan:
    def test_empty_db_returns_200(self, client: TestClient) -> None:
        assert client.post("/agent/scan").status_code == 200

    def test_empty_db_counts_zero(self, client: TestClient) -> None:
        data = client.post("/agent/scan").json()
        assert data == {"scanned": 0, "created": 0, "skipped": 0}

    def test_creates_one_campaign_per_player(
        self, client: TestClient, session: Session
    ) -> None:
        session.add(_make_player("p_001"))
        session.add(_make_player("p_002"))
        session.commit()

        data = client.post("/agent/scan").json()
        assert data["scanned"] == 2
        assert data["created"] == 2
        assert data["skipped"] == 0

    def test_campaign_stored_in_db(
        self, client: TestClient, session: Session
    ) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        client.post("/agent/scan")

        session.expire_all()
        rows = session.exec(select(Campaign).where(Campaign.player_id == "p_001")).all()
        assert len(rows) == 1

    def test_campaign_has_cohort(self, client: TestClient, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        client.post("/agent/scan")

        session.expire_all()
        c = session.exec(select(Campaign).where(Campaign.player_id == "p_001")).first()
        assert c is not None and c.cohort

    def test_campaign_has_offer_json(self, client: TestClient, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        client.post("/agent/scan")

        session.expire_all()
        c = session.exec(select(Campaign).where(Campaign.player_id == "p_001")).first()
        assert c is not None and c.offer_json is not None
        offer = json.loads(c.offer_json)
        assert "type" in offer and "copy" in offer

    def test_campaign_has_reasoning_json(
        self, client: TestClient, session: Session
    ) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        client.post("/agent/scan")

        session.expire_all()
        c = session.exec(select(Campaign).where(Campaign.player_id == "p_001")).first()
        assert c is not None and c.reasoning_json is not None
        reasoning = json.loads(c.reasoning_json)
        assert isinstance(reasoning, list) and reasoning

    def test_idempotent_second_scan_skips(
        self, client: TestClient, session: Session
    ) -> None:
        session.add(_make_player("p_001"))
        session.commit()

        r1 = client.post("/agent/scan")
        r2 = client.post("/agent/scan")
        assert r1.json()["created"] == 1
        assert r2.json()["created"] == 0
        assert r2.json()["skipped"] == 1

    def test_idempotent_no_duplicate_campaigns(
        self, client: TestClient, session: Session
    ) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        client.post("/agent/scan")
        client.post("/agent/scan")

        session.expire_all()
        rows = session.exec(select(Campaign).where(Campaign.player_id == "p_001")).all()
        assert len(rows) == 1

    def test_new_campaign_after_terminal_status(
        self, client: TestClient, session: Session
    ) -> None:
        session.add(_make_player("p_001"))
        session.commit()

        client.post("/agent/scan")

        # Mark existing campaign as delivered (terminal)
        session.expire_all()
        c = session.exec(select(Campaign).where(Campaign.player_id == "p_001")).first()
        assert c is not None
        c.status = CampaignStatus.delivered
        session.add(c)
        session.commit()

        # Next scan must create a fresh campaign
        r2 = client.post("/agent/scan")
        assert r2.json()["created"] == 1


# ── GET /agent/decide/{player_id} ─────────────────────────────────────────────


class TestDecide:
    def test_unknown_player_returns_404(self, client: TestClient) -> None:
        assert client.get("/agent/decide/nonexistent").status_code == 404

    def test_returns_200(self, client: TestClient, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        assert client.get("/agent/decide/p_001").status_code == 200

    def test_has_all_top_level_keys(
        self, client: TestClient, session: Session
    ) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        data = client.get("/agent/decide/p_001").json()
        for key in (
            "player_id",
            "campaign_id",
            "cohort",
            "risk_score",
            "reasoning",
            "offer",
            "script",
        ):
            assert key in data, f"Missing key: {key}"

    def test_player_id_in_response_matches(
        self, client: TestClient, session: Session
    ) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        data = client.get("/agent/decide/p_001").json()
        assert data["player_id"] == "p_001"

    def test_script_has_4_scenes(self, client: TestClient, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        data = client.get("/agent/decide/p_001").json()
        assert len(data["script"]["scenes"]) == 4

    def test_script_scene_types_in_order(
        self, client: TestClient, session: Session
    ) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        data = client.get("/agent/decide/p_001").json()
        types = [s["type"] for s in data["script"]["scenes"]]
        assert types == ["intro", "personalized_hook", "offer", "cta"]

    def test_reasoning_non_empty(self, client: TestClient, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        data = client.get("/agent/decide/p_001").json()
        assert data["reasoning"]

    def test_risk_score_in_range(self, client: TestClient, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        data = client.get("/agent/decide/p_001").json()
        assert 0 <= data["risk_score"] <= 100

    def test_offer_has_required_keys(self, client: TestClient, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        data = client.get("/agent/decide/p_001").json()
        for key in ("type", "value", "label", "copy", "terms", "expiry_days", "offer_band"):
            assert key in data["offer"], f"Missing offer key: {key}"

    def test_persists_script_in_campaign(
        self, client: TestClient, session: Session
    ) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        client.get("/agent/decide/p_001")

        session.expire_all()
        c = session.exec(select(Campaign).where(Campaign.player_id == "p_001")).first()
        assert c is not None and c.script_json is not None
        script = json.loads(c.script_json)
        assert "scenes" in script and "full_voiceover_text" in script

    def test_creates_campaign_when_none_exists(
        self, client: TestClient, session: Session
    ) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        client.get("/agent/decide/p_001")

        session.expire_all()
        rows = session.exec(select(Campaign).where(Campaign.player_id == "p_001")).all()
        assert len(rows) == 1

    def test_reuses_campaign_created_by_scan(
        self, client: TestClient, session: Session
    ) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        client.post("/agent/scan")
        client.get("/agent/decide/p_001")

        session.expire_all()
        rows = session.exec(select(Campaign).where(Campaign.player_id == "p_001")).all()
        assert len(rows) == 1

    def test_campaign_id_in_response_is_string(
        self, client: TestClient, session: Session
    ) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        data = client.get("/agent/decide/p_001").json()
        assert isinstance(data["campaign_id"], str) and data["campaign_id"]

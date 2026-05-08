"""Tests for /approval endpoints: queue, approve, reject, edit, regenerate-script."""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401 — ensure tables registered before create_all
from app.db import get_session
from app.main import app
from app.models import Campaign, CampaignStatus, Player

_NOW = datetime(2026, 5, 8, 12, 0, 0, tzinfo=timezone.utc)


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture()
def engine():
    """File-based temp SQLite so FastAPI TestClient threadpool can share the DB."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    url = f"sqlite:///{tmp.name}"
    eng = create_engine(url, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(eng)
    yield eng
    eng.dispose()
    Path(tmp.name).unlink(missing_ok=True)


@pytest.fixture()
def session(engine):
    """A session tied to the test-scoped engine.  Data committed here is visible
    to any other session opened on the same engine (including the one the
    TestClient override creates)."""
    with Session(engine) as sess:
        yield sess


@pytest.fixture()
def client(engine):
    """TestClient with a get_session override that creates a *fresh* session
    from the shared engine.  Never reuse the same session object across
    the seed/read boundary — SQLAlchemy identity-map quirks can hide
    committed rows when the same session is both writer and reader."""
    def override():
        with Session(engine) as sess:
            yield sess

    app.dependency_overrides[get_session] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_session, None)


# ── Seed helpers ────────────────────────────────────────────────────────────


def _seed_player(session: Session, **kwargs) -> Player:
    defaults = {
        "player_id": "p_test",
        "external_id": "ext_test",
        "first_name": "Test",
        "country": "XX",
        "currency": "USD",
        "consent_data_processing": True,
        "consent_video_personalization": True,
        "consent_marketing_communications": True,
        "consent_marketing_email": True,
    }
    defaults.update(kwargs)
    p = Player(**defaults)
    session.add(p)
    session.flush()
    session.commit()
    session.refresh(p)
    return p


def _seed_campaign(
    session: Session,
    player_id: str = "p_test",
    campaign_id: str = "cmp_001",
    status: CampaignStatus = CampaignStatus.draft,
    cohort: str = "casual_dormant",
    risk_score: float = 45.0,
    reasoning_json: str | None = None,
    offer_json: str | None = None,
    script_json: str | None = None,
) -> Campaign:
    c = Campaign(
        campaign_id=campaign_id,
        player_id=player_id,
        cohort=cohort,
        status=status,
        risk_score=risk_score,
        reasoning_json=reasoning_json,
        offer_json=offer_json,
        script_json=script_json,
    )
    session.add(c)
    session.flush()
    session.commit()
    session.refresh(c)
    return c


# ── Queue ───────────────────────────────────────────────────────────────────


class TestQueue:
    def test_empty_queue(self, client):
        r = client.get("/approval/queue")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_draft_and_pending_campaigns(self, session, client):
        _seed_player(session, player_id="p_a")
        _seed_player(session, player_id="p_b")
        _seed_campaign(session, campaign_id="c1", player_id="p_a", status=CampaignStatus.draft)
        _seed_campaign(session, campaign_id="c2", player_id="p_b", status=CampaignStatus.pending_approval)
        _seed_campaign(session, campaign_id="c3", player_id="p_a", status=CampaignStatus.approved)

        r = client.get("/approval/queue")
        assert r.status_code == 200
        data = r.json()
        ids = {item["campaign_id"] for item in data}
        assert ids == {"c1", "c2"}
        assert "c3" not in ids

    def test_includes_player_profile(self, session, client):
        _seed_player(session, player_id="p_x", first_name="Lucas", country="BR", currency="BRL")
        _seed_campaign(session, campaign_id="c_x", player_id="p_x")

        r = client.get("/approval/queue")
        assert r.status_code == 200
        item = r.json()[0]
        assert item["first_name"] == "Lucas"
        assert item["player"]["country"] == "BR"
        assert item["player"]["first_name"] == "Lucas"

    def test_filter_by_cohort(self, session, client):
        _seed_player(session, player_id="p1")
        _seed_player(session, player_id="p2")
        _seed_campaign(session, campaign_id="c1", player_id="p1", cohort="vip_at_risk")
        _seed_campaign(session, campaign_id="c2", player_id="p2", cohort="casual_dormant")

        r = client.get("/approval/queue", params={"cohort": "vip_at_risk"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["cohort"] == "vip_at_risk"

    def test_filter_by_risk_score_min(self, session, client):
        _seed_player(session, player_id="p1")
        _seed_player(session, player_id="p2")
        _seed_campaign(session, campaign_id="c1", player_id="p1", risk_score=30.0)
        _seed_campaign(session, campaign_id="c2", player_id="p2", risk_score=75.0)

        r = client.get("/approval/queue", params={"risk_score_min": 50})
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["campaign_id"] == "c2"

    def test_filter_by_explicit_status(self, session, client):
        _seed_player(session, player_id="p1")
        _seed_campaign(session, campaign_id="c1", player_id="p1", status=CampaignStatus.approved)
        _seed_campaign(session, campaign_id="c2", player_id="p1", status=CampaignStatus.draft)

        r = client.get("/approval/queue", params={"status": "approved"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["campaign_id"] == "c1"

    def test_player_missing_skipped(self, session, client):
        """Campaign with a player_id that does not exist is skipped gracefully."""
        c = Campaign(
            campaign_id="orphan",
            player_id="nonexistent",
            cohort="casual_dormant",
            status=CampaignStatus.draft,
            risk_score=10.0,
        )
        session.add(c)
        session.commit()

        r = client.get("/approval/queue")
        assert r.status_code == 200
        assert r.json() == []

    def test_status_all_returns_every_campaign(self, session, client):
        _seed_player(session, player_id="p1")
        _seed_campaign(session, campaign_id="c1", player_id="p1", status=CampaignStatus.draft)
        _seed_campaign(session, campaign_id="c2", player_id="p1", status=CampaignStatus.approved)
        _seed_campaign(session, campaign_id="c3", player_id="p1", status=CampaignStatus.delivered)

        r = client.get("/approval/queue", params={"status": "all"})
        assert r.status_code == 200
        ids = {item["campaign_id"] for item in r.json()}
        assert ids == {"c1", "c2", "c3"}

    def test_invalid_status_returns_422(self, client):
        r = client.get("/approval/queue", params={"status": "bogus_status"})
        assert r.status_code == 422


# ── Approve ─────────────────────────────────────────────────────────────────


class TestApprove:
    def test_approve_moves_to_approved(self, session, client):
        _seed_player(session)
        _seed_campaign(session, campaign_id="c1", status=CampaignStatus.draft)

        r = client.post("/approval/c1/approve")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "approved"
        assert data["campaign_id"] == "c1"

    def test_approve_already_approved_409(self, session, client):
        _seed_player(session)
        _seed_campaign(session, campaign_id="c1", status=CampaignStatus.approved)

        r = client.post("/approval/c1/approve")
        assert r.status_code == 409

    def test_approve_rejected_409(self, session, client):
        _seed_player(session)
        _seed_campaign(session, campaign_id="c1", status=CampaignStatus.rejected)

        r = client.post("/approval/c1/approve")
        assert r.status_code == 409

    def test_approve_missing_campaign_404(self, client):
        r = client.post("/approval/nonexistent/approve")
        assert r.status_code == 404


# ── Reject ──────────────────────────────────────────────────────────────────


class TestReject:
    def test_reject_stores_reason(self, session, client):
        _seed_player(session)
        _seed_campaign(
            session,
            campaign_id="c1",
            status=CampaignStatus.draft,
            reasoning_json='{"reasoning":"player is dormant"}',
        )

        r = client.post("/approval/c1/reject", json={"reason": "too_aggressive"})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "rejected"
        assert data["reject_reason"] == "too_aggressive"

        # Verify reason is in DB
        session.expire_all()
        updated = session.get(Campaign, 1)
        parsed = json.loads(updated.reasoning_json or "{}")
        assert parsed["reasoning"] == "player is dormant"  # preserved
        assert parsed["reject_reason"] == "too_aggressive"

    def test_reject_missing_reason_422(self, session, client):
        _seed_player(session)
        _seed_campaign(session, campaign_id="c1")

        r = client.post("/approval/c1/reject", json={})
        assert r.status_code == 422

    def test_reject_empty_reason_422(self, session, client):
        _seed_player(session)
        _seed_campaign(session, campaign_id="c1")

        r = client.post("/approval/c1/reject", json={"reason": ""})
        assert r.status_code == 422

    def test_reject_already_delivered_409(self, session, client):
        _seed_player(session)
        _seed_campaign(session, campaign_id="c1", status=CampaignStatus.delivered)

        r = client.post("/approval/c1/reject", json={"reason": "other"})
        assert r.status_code == 409

    def test_reject_already_rejected_409(self, session, client):
        _seed_player(session)
        _seed_campaign(session, campaign_id="c1", status=CampaignStatus.rejected)

        r = client.post("/approval/c1/reject", json={"reason": "wrong_offer"})
        assert r.status_code == 409

    def test_reject_missing_campaign_404(self, client):
        r = client.post("/approval/nonexistent/reject", json={"reason": "other"})
        assert r.status_code == 404

    def test_reject_without_prior_reasoning_json(self, session, client):
        _seed_player(session)
        _seed_campaign(session, campaign_id="c1", reasoning_json=None)

        r = client.post("/approval/c1/reject", json={"reason": "data_issue"})
        assert r.status_code == 200
        session.expire_all()
        updated = session.get(Campaign, 1)
        parsed = json.loads(updated.reasoning_json or "{}")
        assert parsed["reject_reason"] == "data_issue"


# ── Edit ────────────────────────────────────────────────────────────────────


class TestEdit:
    def test_edit_offer_only(self, session, client):
        _seed_player(session)
        _seed_campaign(session, campaign_id="c1", offer_json='{"type":"free_spins","value":30}')

        new_offer = '{"type":"cashback","value":15}'
        r = client.post("/approval/c1/edit", json={"offer_json": new_offer})
        assert r.status_code == 200
        data = r.json()
        assert data["changed"] == ["offer"]
        assert data["auto_approved"] is False

        session.expire_all()
        updated = session.get(Campaign, 1)
        assert updated.offer_json == new_offer

    def test_edit_script_only(self, session, client):
        _seed_player(session)
        _seed_campaign(session, campaign_id="c1", script_json='{"scenes":[]}')

        new_script = '{"scenes":[{"id":1,"type":"intro"}]}'
        r = client.post("/approval/c1/edit", json={"script_json": new_script})
        assert r.status_code == 200
        assert r.json()["changed"] == ["script"]

    def test_edit_both_fields(self, session, client):
        _seed_player(session)
        _seed_campaign(session, campaign_id="c1")
        r = client.post(
            "/approval/c1/edit",
            json={"offer_json": '{"type":"x"}', "script_json": '{"scenes":"y"}'},
        )
        assert r.status_code == 200
        assert set(r.json()["changed"]) == {"offer", "script"}

    def test_edit_with_auto_approve(self, session, client):
        _seed_player(session)
        _seed_campaign(session, campaign_id="c1", status=CampaignStatus.pending_approval)
        r = client.post(
            "/approval/c1/edit",
            json={"offer_json": '{"type":"free_bet"}', "auto_approve": True},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "approved"
        assert r.json()["auto_approved"] is True

    def test_edit_no_fields_400(self, session, client):
        _seed_player(session)
        _seed_campaign(session, campaign_id="c1")
        r = client.post("/approval/c1/edit", json={})
        assert r.status_code == 400

    def test_edit_wrong_status_409(self, session, client):
        _seed_player(session)
        _seed_campaign(session, campaign_id="c1", status=CampaignStatus.approved)
        r = client.post("/approval/c1/edit", json={"offer_json": "{}"})
        assert r.status_code == 409

    def test_edit_missing_campaign_404(self, client):
        r = client.post("/approval/nonexistent/edit", json={"offer_json": "{}"})
        assert r.status_code == 404


# ── Regenerate script ───────────────────────────────────────────────────────


class TestRegenerateScript:
    def test_regenerate_stores_new_script(self, session, client):
        _seed_player(session, player_id="p_x", first_name="Lucas")
        _seed_campaign(
            session,
            campaign_id="c1",
            player_id="p_x",
            cohort="casual_dormant",
            offer_json=json.dumps(
                {"type": "free_spins", "value": 10, "copy": "10 free spins — welcome back"}
            ),
            script_json='{"scenes":[],"full_voiceover_text":"old"}',
        )

        r = client.post("/approval/c1/regenerate-script")
        assert r.status_code == 200
        data = r.json()
        assert data["campaign_id"] == "c1"
        script = data["script"]
        assert len(script["scenes"]) == 4
        assert script["source"] in ("fallback", "llm")
        assert "Lucas" in script["full_voiceover_text"]

        # Check persisted
        session.expire_all()
        updated = session.get(Campaign, 1)
        persisted = json.loads(updated.script_json or "{}")
        assert len(persisted["scenes"]) == 4
        assert persisted["source"] in ("fallback", "llm")

    def test_regenerate_clears_old_script(self, session, client):
        _seed_player(session, player_id="p_y", first_name="Test")
        _seed_campaign(
            session,
            campaign_id="c2",
            player_id="p_y",
            cohort="casual_dormant",
            offer_json=json.dumps({"copy": "test offer"}),
            script_json='{"scenes":[{"id":99,"type":"old"}],"full_voiceover_text":"stale"}',
        )

        r = client.post("/approval/c2/regenerate-script")
        assert r.status_code == 200
        script = r.json()["script"]
        assert script["source"] in ("fallback", "llm")
        assert len(script["scenes"]) == 4

    def test_regenerate_wrong_status_409(self, session, client):
        _seed_player(session, player_id="p_z")
        _seed_campaign(
            session,
            campaign_id="c3",
            player_id="p_z",
            cohort="casual_dormant",
            status=CampaignStatus.approved,
        )
        r = client.post("/approval/c3/regenerate-script")
        assert r.status_code == 409

    def test_regenerate_missing_campaign_404(self, client):
        r = client.post("/approval/nonexistent/regenerate-script")
        assert r.status_code == 404

    def test_regenerate_preserves_offer(self, session, client):
        """Regenerate should not touch offer_json."""
        _seed_player(session, player_id="p_w", first_name="Test")
        original_offer = json.dumps(
            {"type": "cashback", "value": 15, "copy": "15% cashback"}
        )
        _seed_campaign(
            session,
            campaign_id="c4",
            player_id="p_w",
            cohort="high_value_dormant",
            offer_json=original_offer,
        )

        r = client.post("/approval/c4/regenerate-script")
        assert r.status_code == 200

        session.expire_all()
        updated = session.get(Campaign, 1)
        assert updated.offer_json == original_offer


# ── Integration: full approval flow ─────────────────────────────────────────


class TestApprovalFlow:
    def test_draft_to_approved(self, session, client):
        _seed_player(session, player_id="p_a")
        _seed_campaign(session, campaign_id="flow1", player_id="p_a", status=CampaignStatus.draft)

        # 1. In queue
        r = client.get("/approval/queue")
        assert len(r.json()) == 1
        assert r.json()[0]["status"] == "draft"

        # 2. Edit offer
        r = client.post(
            "/approval/flow1/edit",
            json={"offer_json": '{"type":"deposit_match","value":100}', "auto_approve": True},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "approved"

        # 3. Gone from queue
        r = client.get("/approval/queue")
        assert r.json() == []

    def test_draft_to_rejected(self, session, client):
        _seed_player(session, player_id="p_b")
        _seed_campaign(session, campaign_id="flow2", player_id="p_b")

        r = client.post("/approval/flow2/reject", json={"reason": "wrong_tone"})
        assert r.status_code == 200
        assert r.json()["status"] == "rejected"

        # Gone from default queue, but visible with explicit status filter
        r = client.get("/approval/queue", params={"status": "rejected"})
        assert len(r.json()) == 1
        assert r.json()[0]["status"] == "rejected"

"""Tests for GET /metrics/dashboard."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401
from app.db import get_session
from app.main import app
from app.models import Campaign, CampaignStatus, Tracking


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
def client(engine):
    def override():
        with Session(engine) as sess:
            yield sess

    app.dependency_overrides[get_session] = override
    yield TestClient(app)
    app.dependency_overrides.pop(get_session, None)


class TestMetricsDashboard:
    def test_empty_db_returns_zeros(self, client):
        r = client.get("/metrics/dashboard")
        assert r.status_code == 200
        d = r.json()
        assert d["funnel"]["scanned"] == 0
        assert d["funnel"]["deposited"] == 0
        assert d["kpis"]["total_players"] == 0
        assert d["kpis"]["approval_rate"] == 0.0
        assert d["cohort_breakdown"] == []

    def test_funnel_counts(self, client, engine):
        with Session(engine) as s:
            # delivered → in approved + delivered; converted → in approved + delivered
            s.add(Campaign(campaign_id="c1", player_id="p1", cohort="casual_dormant", status=CampaignStatus.delivered))
            s.add(Campaign(campaign_id="c2", player_id="p2", cohort="casual_dormant", status=CampaignStatus.converted))
            # pending_approval → NOT in approved/delivered
            s.add(Campaign(campaign_id="c3", player_id="p3", cohort="high_value_dormant", status=CampaignStatus.pending_approval))
            s.add(Tracking(campaign_id="c1", event_type="video_play"))
            s.add(Tracking(campaign_id="c2", event_type="video_play"))
            s.add(Tracking(campaign_id="c2", event_type="cta_click"))
            s.commit()

        r = client.get("/metrics/dashboard")
        assert r.status_code == 200
        f = r.json()["funnel"]
        assert f["scanned"] == 3
        assert f["approved"] == 2
        assert f["delivered"] == 2
        assert f["played"] == 2
        assert f["clicked"] == 1
        assert f["deposited"] == 1

    def test_kpis(self, client, engine):
        with Session(engine) as s:
            s.add(Campaign(campaign_id="c1", player_id="p1", cohort="casual_dormant", status=CampaignStatus.delivered))
            s.add(Campaign(campaign_id="c2", player_id="p2", cohort="casual_dormant", status=CampaignStatus.converted))
            s.add(Tracking(campaign_id="c1", event_type="video_play"))
            s.add(Tracking(campaign_id="c2", event_type="video_play"))
            s.add(Tracking(campaign_id="c2", event_type="cta_click"))
            s.commit()

        r = client.get("/metrics/dashboard")
        assert r.status_code == 200
        k = r.json()["kpis"]
        assert k["total_players"] == 2
        assert k["campaigns_created"] == 2
        assert k["videos_delivered"] == 2
        assert k["approval_rate"] == 1.0
        assert k["avg_ctr"] == 0.5      # 1 click / 2 plays
        assert k["reactivation_rate"] == 0.5  # 1 converted / 2 delivered

    def test_cohort_breakdown(self, client, engine):
        with Session(engine) as s:
            s.add(Campaign(campaign_id="c1", player_id="p1", cohort="casual_dormant", status=CampaignStatus.delivered))
            s.add(Campaign(campaign_id="c2", player_id="p2", cohort="casual_dormant", status=CampaignStatus.converted))
            s.add(Campaign(campaign_id="c3", player_id="p3", cohort="high_value_dormant", status=CampaignStatus.approved))
            s.commit()

        r = client.get("/metrics/dashboard")
        assert r.status_code == 200
        rows = {row["cohort"]: row for row in r.json()["cohort_breakdown"]}
        assert "casual_dormant" in rows
        assert rows["casual_dormant"]["count"] == 2
        assert rows["casual_dormant"]["delivered"] == 2
        assert rows["casual_dormant"]["converted"] == 1
        assert "high_value_dormant" in rows
        assert rows["high_value_dormant"]["count"] == 1
        assert rows["high_value_dormant"]["approved"] == 1
        assert rows["high_value_dormant"]["converted"] == 0

    def test_approval_rate_partial(self, client, engine):
        with Session(engine) as s:
            s.add(Campaign(campaign_id="c1", player_id="p1", cohort="casual_dormant", status=CampaignStatus.pending_approval))
            s.add(Campaign(campaign_id="c2", player_id="p2", cohort="casual_dormant", status=CampaignStatus.approved))
            s.commit()

        r = client.get("/metrics/dashboard")
        assert r.status_code == 200
        k = r.json()["kpis"]
        assert k["approval_rate"] == 0.5

    def test_duplicate_tracking_events_counted_once(self, client, engine):
        """Multiple play events for the same campaign count as one played campaign."""
        with Session(engine) as s:
            s.add(Campaign(campaign_id="c1", player_id="p1", cohort="casual_dormant", status=CampaignStatus.delivered))
            s.add(Tracking(campaign_id="c1", event_type="video_play"))
            s.add(Tracking(campaign_id="c1", event_type="video_play"))  # duplicate
            s.commit()

        r = client.get("/metrics/dashboard")
        assert r.status_code == 200
        assert r.json()["funnel"]["played"] == 1  # deduped by campaign_id

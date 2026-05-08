"""Tests for POST /delivery/send orchestration."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

import app.models  # noqa: F401
from app.db import get_session
from app.main import app
from app.models import Campaign, CampaignStatus, Delivery, Player, VideoAsset


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


# ── Seed helpers ────────────────────────────────────────────────────────────


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
        "preferred_channels": json.dumps(["telegram", "email"]),
    }
    defaults.update(overrides)
    return Player(**defaults)


def _campaign(**overrides) -> Campaign:
    defaults = {
        "campaign_id": "cmp_test",
        "player_id": "p_test",
        "cohort": "casual_dormant",
        "status": CampaignStatus.ready,
        "risk_score": 45.0,
    }
    defaults.update(overrides)
    return Campaign(**defaults)


def _asset(campaign_id: str = "cmp_test", poster_url: str | None = "https://img/poster.jpg") -> VideoAsset:
    return VideoAsset(
        campaign_id=campaign_id,
        poster_url=poster_url,
        video_url="https://vid/video.mp4",
        status="ready",
    )


def _seed(session: Session, player_kw=None, campaign_kw=None, asset: VideoAsset | None = True):
    """Seed player + campaign + optional asset. Returns (player, campaign, asset)."""
    p = _player(**(player_kw or {}))
    session.add(p)
    c = _campaign(player_id=p.player_id, **(campaign_kw or {}))
    session.add(c)
    a = None
    if asset is not False:
        a_v = asset if isinstance(asset, VideoAsset) else _asset(campaign_id=c.campaign_id)
        session.add(a_v)
        a = a_v
    session.flush()
    session.commit()
    return p, c, a


def _delivery_count(session: Session, campaign_id: str) -> int:
    return len(session.exec(select(Delivery).where(Delivery.campaign_id == campaign_id)).all())


# ── Tests ───────────────────────────────────────────────────────────────────


class TestSendNotFound:
    def test_campaign_not_found(self, session, client):
        r = client.post("/delivery/send", json={"campaign_id": "nonexistent"})
        assert r.status_code == 404

    def test_player_not_found(self, session, client):
        c = _campaign(campaign_id="orphan", player_id="no_player")
        session.add(c)
        session.commit()
        r = client.post("/delivery/send", json={"campaign_id": "orphan"})
        assert r.status_code == 404


class TestSendReadinessGate:
    def test_wrong_status_rejected(self, session, client):
        _seed(session, campaign_kw={"status": CampaignStatus.draft})
        r = client.post("/delivery/send", json={"campaign_id": "cmp_test"})
        assert r.status_code == 409

    @pytest.mark.asyncio
    async def test_status_approved_allowed(self, session, client):
        _seed(session, campaign_kw={"status": CampaignStatus.approved})

        mock_bot = MagicMock()
        mock_msg = MagicMock()
        mock_msg.message_id = 1
        mock_bot.send_photo = AsyncMock(return_value=mock_msg)
        mock_bot.send_message = AsyncMock(return_value=mock_msg)

        from app.api.delivery import _build_telegram
        from app.delivery.telegram_adapter import TelegramAdapter

        app.dependency_overrides[_build_telegram] = lambda: TelegramAdapter(bot=mock_bot)
        try:
            r = client.post("/delivery/send", json={"campaign_id": "cmp_test"})
            assert r.status_code == 200
        finally:
            app.dependency_overrides.pop(_build_telegram, None)


class TestGenerationConsentBlock:
    def test_missing_data_processing_blocks(self, session, client):
        _seed(session, player_kw={"consent_data_processing": False})
        r = client.post("/delivery/send", json={"campaign_id": "cmp_test"})
        assert r.status_code == 200
        data = r.json()
        assert data["overall_status"] == "blocked"
        assert any("data_processing" in (c.get("reason", "") or "") for c in data["channels"])

    def test_missing_video_personalization_blocks(self, session, client):
        _seed(session, player_kw={"consent_video_personalization": False})
        r = client.post("/delivery/send", json={"campaign_id": "cmp_test"})
        assert r.status_code == 200
        data = r.json()
        assert data["overall_status"] == "blocked"
        assert any("video_personalization" in (c.get("reason", "") or "") for c in data["channels"])


class TestNoReachableChannel:
    def test_no_marketing_consent_blocks(self, session, client):
        _seed(session, player_kw={
            "consent_marketing_communications": False,
            "telegram_chat_id": None,
            "email": None,
        })
        r = client.post("/delivery/send", json={"campaign_id": "cmp_test"})
        assert r.status_code == 200
        data = r.json()
        assert data["overall_status"] == "blocked"

        # Campaign status updated
        session.expire_all()
        c = session.get(Campaign, 1)
        assert c.status == CampaignStatus.ready_blocked_delivery

    def test_campaign_marked_ready_blocked_delivery(self, session, client):
        _seed(session, player_kw={
            "telegram_chat_id": None,
            "email": None,
        })
        assert client.post("/delivery/send", json={"campaign_id": "cmp_test"}).status_code == 200
        session.expire_all()
        c = session.get(Campaign, 1)
        assert c.status == CampaignStatus.ready_blocked_delivery


class TestMockTelegramGuard:
    def test_mock_tg_id_skipped(self, session, client):
        _seed(session, player_kw={"telegram_chat_id": "mock_tg_001", "email": None})
        r = client.post("/delivery/send", json={"campaign_id": "cmp_test"})
        assert r.status_code == 200
        data = r.json()
        assert data["overall_status"] == "blocked"
        assert any("mock_telegram_chat_id" in (c.get("reason", "") or "") for c in data["channels"])

        # Delivery row persisted
        assert _delivery_count(session, "cmp_test") == 1


class TestTelegramDelivery:
    @pytest.mark.asyncio
    async def test_real_telegram_send(self, session, client):
        _seed(session, player_kw={"telegram_chat_id": "111222333", "email": None})

        # Override the Telegram adapter factory with a mock
        mock_bot = MagicMock()
        mock_msg = MagicMock()
        mock_msg.message_id = 42
        mock_bot.send_photo = AsyncMock(return_value=mock_msg)

        from app.api.delivery import _build_telegram
        from app.delivery.telegram_adapter import TelegramAdapter

        mock_adapter = TelegramAdapter(bot=mock_bot)

        def override_build_telegram():
            return mock_adapter

        app.dependency_overrides[_build_telegram] = override_build_telegram

        try:
            r = client.post("/delivery/send", json={"campaign_id": "cmp_test"})
            assert r.status_code == 200
            data = r.json()
            assert data["overall_status"] == "sent"
            assert data["channels"][0]["channel"] == "telegram"
            assert data["channels"][0]["status"] == "sent"
            assert data["channels"][0]["message_id"] == "42"

            # Delivery row persisted
            assert _delivery_count(session, "cmp_test") == 1

            # Campaign status updated
            session.expire_all()
            c = session.get(Campaign, 1)
            assert c.status == CampaignStatus.delivered
        finally:
            app.dependency_overrides.pop(_build_telegram, None)

    @pytest.mark.asyncio
    async def test_telegram_adapter_send_called_with_correct_params(self, session, client):
        """Verify adapter.send() receives the right player, campaign, and asset."""
        _seed(session, player_kw={"telegram_chat_id": "111222333", "email": None})

        mock_bot = MagicMock()
        mock_msg = MagicMock()
        mock_msg.message_id = 77
        mock_bot.send_photo = AsyncMock(return_value=mock_msg)

        from app.api.delivery import _build_telegram
        from app.delivery.telegram_adapter import TelegramAdapter

        mock_adapter = TelegramAdapter(bot=mock_bot)

        def override_build_telegram():
            return mock_adapter

        app.dependency_overrides[_build_telegram] = override_build_telegram

        try:
            r = client.post("/delivery/send", json={"campaign_id": "cmp_test"})
            assert r.status_code == 200
            data = r.json()
            assert data["channels"][0]["message_id"] == "77"
            assert data["channels"][0]["recipient"] == "111222333"

            # Verify send_photo was called with correct args
            mock_bot.send_photo.assert_awaited_once()
            call_kwargs = mock_bot.send_photo.await_args.kwargs
            assert call_kwargs["chat_id"] == 111222333
            assert "poster.jpg" in call_kwargs["photo"]
        finally:
            app.dependency_overrides.pop(_build_telegram, None)


class TestEmailDelivery:
    @pytest.mark.asyncio
    async def test_email_prepared(self, session, client):
        _seed(session, player_kw={
            "telegram_chat_id": None,
            "email": "player@test.com",
            "preferred_channels": json.dumps(["email"]),
        })

        from app.api.delivery import _build_email
        from app.delivery.email_adapter import EmailPosterAdapter

        mock_adapter = EmailPosterAdapter()

        def override_build_email():
            return mock_adapter

        app.dependency_overrides[_build_email] = override_build_email

        try:
            r = client.post("/delivery/send", json={"campaign_id": "cmp_test"})
            assert r.status_code == 200
            data = r.json()
            assert data["overall_status"] == "prepared"
            assert data["channels"][0]["channel"] == "email"
            assert data["channels"][0]["status"] == "prepared"
            assert data["channels"][0]["recipient"] == "player@test.com"

            assert _delivery_count(session, "cmp_test") == 1
        finally:
            app.dependency_overrides.pop(_build_email, None)

    @pytest.mark.asyncio
    async def test_email_blocked_no_consent(self, session, client):
        _seed(session, player_kw={
            "telegram_chat_id": None,
            "email": "player@test.com",
            "consent_marketing_email": False,
            "preferred_channels": json.dumps(["email"]),
        })

        from app.api.delivery import _build_email
        from app.delivery.email_adapter import EmailPosterAdapter

        def override_build_email():
            return EmailPosterAdapter()

        app.dependency_overrides[_build_email] = override_build_email

        try:
            r = client.post("/delivery/send", json={"campaign_id": "cmp_test"})
            assert r.status_code == 200
            data = r.json()
            assert data["overall_status"] == "blocked"
        finally:
            app.dependency_overrides.pop(_build_email, None)


class TestChannelSelection:
    def test_telegram_preferred_over_email(self, session, client):
        """When both Telegram and email are available, Telegram is preferred."""
        _seed(session, player_kw={
            "telegram_chat_id": "111",
            "email": "player@test.com",
            "preferred_channels": json.dumps(["telegram", "email"]),
        })

        mock_bot = MagicMock()
        mock_msg = MagicMock()
        mock_msg.message_id = 1
        mock_bot.send_photo = AsyncMock(return_value=mock_msg)

        from app.api.delivery import _build_telegram
        from app.delivery.telegram_adapter import TelegramAdapter

        app.dependency_overrides[_build_telegram] = lambda: TelegramAdapter(bot=mock_bot)

        try:
            r = client.post("/delivery/send", json={"campaign_id": "cmp_test"})
            assert r.status_code == 200
            data = r.json()
            # Should use Telegram, not email
            assert data["channels"][0]["channel"] == "telegram"
        finally:
            app.dependency_overrides.pop(_build_telegram, None)


class TestDeliveryRowPersistence:
    def test_blocked_row_persisted(self, session, client):
        _seed(session, player_kw={"consent_data_processing": False})
        r = client.post("/delivery/send", json={"campaign_id": "cmp_test"})
        assert r.status_code == 200
        assert _delivery_count(session, "cmp_test") == 1

        delivery = session.exec(
            select(Delivery).where(Delivery.campaign_id == "cmp_test")
        ).first()
        assert delivery is not None
        assert delivery.status == "blocked"
        assert delivery.failure_reason is not None
        assert "data_processing" in delivery.failure_reason


class TestCrmWriteback:
    def test_writeback_called_on_block(self, session, client, monkeypatch):
        called = []

        def fake_write_delivery(campaign_id, channel, status, recipient=None):
            called.append((campaign_id, channel, status, recipient))
            return {}

        monkeypatch.setattr("app.delivery.crm_writeback.CrmWritebackAdapter.write_delivery", fake_write_delivery)

        _seed(session, player_kw={"consent_data_processing": False})
        r = client.post("/delivery/send", json={"campaign_id": "cmp_test"})
        assert r.status_code == 200

        # CrmWriteback called after the Delivery row
        assert len(called) >= 1


class TestNoAsset:
    @pytest.mark.asyncio
    async def test_send_without_asset(self, session, client):
        """Send should work even if no VideoAsset exists — adapter handles None asset."""
        _seed(session, player_kw={"telegram_chat_id": "111", "email": None}, asset=False)

        mock_bot = MagicMock()
        mock_msg = MagicMock()
        mock_msg.message_id = 99
        mock_bot.send_message = AsyncMock(return_value=mock_msg)

        from app.api.delivery import _build_telegram
        from app.delivery.telegram_adapter import TelegramAdapter

        app.dependency_overrides[_build_telegram] = lambda: TelegramAdapter(bot=mock_bot)

        try:
            r = client.post("/delivery/send", json={"campaign_id": "cmp_test"})
            assert r.status_code == 200
            assert r.json()["overall_status"] == "sent"
        finally:
            app.dependency_overrides.pop(_build_telegram, None)

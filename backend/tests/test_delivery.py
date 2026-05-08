import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import Message as AiogramMessage

from app.delivery.adapters import DeliveryAdapter, DeliveryResult, DeliveryStatus
from app.delivery.crm_writeback import CrmWritebackAdapter
from app.delivery.eligibility import (
    block_reason,
    build_delivery_block_reason,
    can_send_any_channel,
    can_send_channel,
    check_delivery_consent,
    check_generation_consent,
    generation_block_reason,
    get_available_channels,
    select_best_channel,
)
from app.delivery.email_adapter import EmailPosterAdapter
from app.delivery.landing_adapter import LandingTrackingAdapter
from app.delivery.telegram_adapter import TelegramAdapter
from app.models import Campaign, Player


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _player(**overrides) -> Player:
    defaults: dict = {
        "player_id": "p_test",
        "external_id": "ext_test",
        "first_name": "Test",
        "preferred_channels": json.dumps(["telegram", "email"]),
        "telegram_chat_id": "123456",
        "email": "test@example.com",
        "consent_marketing_communications": True,
        "consent_marketing_email": True,
        "consent_marketing_sms": False,
        "consent_whatsapp_business": False,
        "consent_push_notifications": False,
        "consent_video_personalization": True,
        "consent_data_processing": True,
    }
    defaults.update(overrides)
    return Player(**defaults)


def _campaign(**overrides) -> Campaign:
    defaults: dict = {
        "campaign_id": "cmp_test",
        "player_id": "p_test",
        "cohort": "casual_dormant",
        "status": "ready",
        "risk_score": 45.0,
    }
    defaults.update(overrides)
    return Campaign(**defaults)


# ---------------------------------------------------------------------------
# generation consent
# ---------------------------------------------------------------------------

class TestGenerationConsent:
    def test_full_consent_passes(self):
        p = _player(
            consent_data_processing=True,
            consent_video_personalization=True,
        )
        assert check_generation_consent(p) is True
        assert generation_block_reason(p) is None

    def test_missing_data_processing_blocks(self):
        p = _player(
            consent_data_processing=False,
            consent_video_personalization=True,
        )
        assert check_generation_consent(p) is False
        reason = generation_block_reason(p)
        assert "data_processing" in reason
        assert "video_personalization" not in reason

    def test_missing_video_personalization_blocks(self):
        p = _player(
            consent_data_processing=True,
            consent_video_personalization=False,
        )
        assert check_generation_consent(p) is False
        reason = generation_block_reason(p)
        assert "video_personalization" in reason

    def test_both_missing_blocks(self):
        p = _player(
            consent_data_processing=False,
            consent_video_personalization=False,
        )
        assert check_generation_consent(p) is False
        reason = generation_block_reason(p)
        assert "data_processing" in reason
        assert "video_personalization" in reason


# ---------------------------------------------------------------------------
# delivery consent & channel availability
# ---------------------------------------------------------------------------

class TestDeliveryConsent:
    def test_marketing_communications_false_blocks_all(self):
        p = _player(consent_marketing_communications=False)
        assert check_delivery_consent(p) is False
        assert get_available_channels(p) == []
        assert can_send_any_channel(p) is False

    def test_marketing_communications_true_allows_channels(self):
        p = _player(consent_marketing_communications=True)
        assert check_delivery_consent(p) is True
        assert len(get_available_channels(p)) > 0


class TestGetAvailableChannels:
    def test_full_player_telegram_and_email(self):
        p = _player()
        channels = get_available_channels(p)
        assert "telegram" in channels
        assert "email" in channels

    def test_no_telegram_chat_id_excludes_telegram(self):
        p = _player(telegram_chat_id=None)
        channels = get_available_channels(p)
        assert "telegram" not in channels
        assert "email" in channels

    def test_no_email_excludes_email(self):
        p = _player(email=None)
        channels = get_available_channels(p)
        assert "telegram" in channels
        assert "email" not in channels

    def test_email_consent_false_excludes_email(self):
        p = _player(consent_marketing_email=False)
        channels = get_available_channels(p)
        assert "telegram" in channels
        assert "email" not in channels

    def test_no_marketing_communications_returns_empty(self):
        p = _player(consent_marketing_communications=False)
        assert get_available_channels(p) == []

    def test_preferred_channels_order_respected(self):
        p = _player(preferred_channels=json.dumps(["email", "telegram"]))
        channels = get_available_channels(p)
        assert channels == ["email", "telegram"]

    def test_preferred_partial_match(self):
        p = _player(
            preferred_channels=json.dumps(["whatsapp", "email", "telegram"]),
            consent_whatsapp_business=False,
            phone_e164=None,
        )
        channels = get_available_channels(p)
        assert channels == ["email", "telegram"]
        assert "whatsapp" not in channels

    def test_no_preferred_falls_back_to_all_available(self):
        p = _player(preferred_channels=None)
        channels = get_available_channels(p)
        assert "telegram" in channels
        assert "email" in channels

    def test_invalid_preferred_json_falls_back(self):
        p = _player(preferred_channels="{bad json")
        channels = get_available_channels(p)
        assert len(channels) == 2

    def test_sms_available_when_consented_and_has_phone(self):
        p = _player(
            phone_e164="+447000000005",
            consent_marketing_sms=True,
            preferred_channels=json.dumps(["telegram", "email", "sms"]),
        )
        channels = get_available_channels(p)
        assert "sms" in channels

    def test_whatsapp_available_when_consented_and_has_phone(self):
        p = _player(
            phone_e164="+447000000005",
            consent_whatsapp_business=True,
            preferred_channels=json.dumps(["telegram", "email", "whatsapp"]),
        )
        channels = get_available_channels(p)
        assert "whatsapp" in channels

    def test_push_available_when_consented_and_has_token(self):
        p = _player(
            push_token="mock_token",
            consent_push_notifications=True,
            preferred_channels=json.dumps(["telegram", "email", "push"]),
        )
        channels = get_available_channels(p)
        assert "push" in channels


# ---------------------------------------------------------------------------
# can_send_channel
# ---------------------------------------------------------------------------

class TestCanSendChannel:
    def test_telegram_requires_chat_id(self):
        p_tg = _player(telegram_chat_id="123")
        p_no = _player(telegram_chat_id=None)
        assert can_send_channel(p_tg, "telegram") is True
        assert can_send_channel(p_no, "telegram") is False

    def test_telegram_requires_marketing_consent(self):
        p = _player(consent_marketing_communications=False)
        assert can_send_channel(p, "telegram") is False

    def test_email_requires_address_and_consent(self):
        ok = _player(email="ok@test.com", consent_marketing_email=True)
        no_addr = _player(email=None, consent_marketing_email=True)
        no_consent = _player(email="ok@test.com", consent_marketing_email=False)
        assert can_send_channel(ok, "email") is True
        assert can_send_channel(no_addr, "email") is False
        assert can_send_channel(no_consent, "email") is False

    def test_unknown_channel_returns_false(self):
        p = _player()
        assert can_send_channel(p, "fax") is False


# ---------------------------------------------------------------------------
# select_best_channel / can_send_any_channel / block_reason
# ---------------------------------------------------------------------------

class TestSelectBestChannel:
    def test_telegram_first_by_default(self):
        p = _player()
        assert select_best_channel(p) == "telegram"

    def test_email_fallback_when_no_telegram(self):
        p = _player(telegram_chat_id=None)
        assert select_best_channel(p) == "email"

    def test_none_when_no_channels(self):
        p = _player(
            telegram_chat_id=None,
            email=None,
            consent_marketing_communications=False,
        )
        assert select_best_channel(p) is None


class TestCanSendAnyChannel:
    def test_true_when_channels_available(self):
        p = _player()
        assert can_send_any_channel(p) is True

    def test_false_when_blocked(self):
        p = _player(consent_marketing_communications=False)
        assert can_send_any_channel(p) is False


class TestBlockReason:
    def test_telegram_block_no_chat_id(self):
        p = _player(telegram_chat_id=None)
        assert block_reason(p, "telegram") == "blocked_no_telegram_chat_id"

    def test_telegram_ok_returns_none(self):
        p = _player(telegram_chat_id="123")
        assert block_reason(p, "telegram") is None

    def test_email_block_no_address(self):
        p = _player(email=None)
        assert block_reason(p, "email") == "blocked_no_email_identifier"

    def test_email_block_no_consent(self):
        p = _player(consent_marketing_email=False)
        assert block_reason(p, "email") == "blocked_no_email_consent"

    def test_block_no_marketing_consent_overrides(self):
        p = _player(consent_marketing_communications=False)
        assert block_reason(p, "telegram") == "blocked_no_marketing_consent"

    def test_unknown_channel(self):
        p = _player()
        assert "unknown" in block_reason(p, "fax")

    def test_sms_block(self):
        p = _player(phone_e164=None)
        assert block_reason(p, "sms") == "blocked_no_phone_identifier"


class TestBuildDeliveryBlockReason:
    def test_ready_when_channels_available(self):
        p = _player()
        assert build_delivery_block_reason(p) is None

    def test_blocked_no_consent(self):
        p = _player(consent_marketing_communications=False)
        assert build_delivery_block_reason(p) == "blocked_no_marketing_consent"

    def test_blocked_no_reachable_channel(self):
        p = _player(
            telegram_chat_id=None,
            email=None,
            consent_marketing_communications=True,
        )
        assert build_delivery_block_reason(p) == "blocked_no_reachable_channel"


# ---------------------------------------------------------------------------
# TelegramAdapter
# ---------------------------------------------------------------------------

class TestTelegramAdapter:
    def test_can_send_true(self):
        p = _player(telegram_chat_id="123")
        c = _campaign()
        adapter = TelegramAdapter()
        assert adapter.can_send(p, c) is True

    def test_can_send_false_no_chat_id(self):
        p = _player(telegram_chat_id=None)
        c = _campaign()
        adapter = TelegramAdapter()
        assert adapter.can_send(p, c) is False

    def test_can_send_false_no_marketing_consent(self):
        p = _player(consent_marketing_communications=False)
        c = _campaign()
        adapter = TelegramAdapter()
        assert adapter.can_send(p, c) is False

    @pytest.mark.asyncio
    async def test_send_blocked_player_returns_skipped(self):
        p = _player(telegram_chat_id=None)
        c = _campaign()
        adapter = TelegramAdapter()
        result = await adapter.send(p, c)
        assert result.status == "skipped"
        assert result.channel == "telegram"
        assert "blocked" in (result.reason or "")

    @pytest.mark.asyncio
    async def test_send_uses_injected_bot(self):
        mock_bot = MagicMock(spec=["send_photo"])
        mock_msg = MagicMock(spec=AiogramMessage)
        mock_msg.message_id = 999
        mock_bot.send_photo = AsyncMock(return_value=mock_msg)

        p = _player(telegram_chat_id="111")
        c = _campaign(campaign_id="cmp_abc")

        from app.models import VideoAsset

        asset = VideoAsset(campaign_id="cmp_abc", poster_url="https://example.com/poster.jpg")

        adapter = TelegramAdapter(bot=mock_bot)
        result = await adapter.send(p, c, asset=asset)

        assert result.status == "sent"
        assert result.message_id == "999"
        mock_bot.send_photo.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_without_poster_falls_back_to_message(self):
        mock_bot = MagicMock(spec=["send_message"])
        mock_msg = MagicMock(spec=AiogramMessage)
        mock_msg.message_id = 42
        mock_bot.send_message = AsyncMock(return_value=mock_msg)

        p = _player(telegram_chat_id="111")
        c = _campaign(campaign_id="cmp_xyz")

        adapter = TelegramAdapter(bot=mock_bot)
        result = await adapter.send(p, c)

        assert result.status == "sent"
        assert result.message_id == "42"
        mock_bot.send_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_with_offer_json_includes_caption(self):
        mock_bot = MagicMock(spec=["send_photo"])
        mock_msg = MagicMock(spec=AiogramMessage)
        mock_msg.message_id = 1
        mock_bot.send_photo = AsyncMock(return_value=mock_msg)

        from app.models import VideoAsset

        asset = VideoAsset(campaign_id="cmp_abc", poster_url="https://example.com/poster.jpg")

        offer = {"type": "free_spins", "description": "30 free spins on Fruit Slots"}
        p = _player(telegram_chat_id="111")
        c = _campaign(campaign_id="cmp_abc", offer_json=json.dumps(offer))

        adapter = TelegramAdapter(bot=mock_bot)
        result = await adapter.send(p, c, asset=asset)

        assert result.status == "sent"
        call_args = mock_bot.send_photo.await_args
        assert call_args is not None
        caption = call_args.kwargs.get("caption", "")
        assert "30 free spins" in caption
        assert "cmp_abc" in caption

    @pytest.mark.asyncio
    async def test_get_status(self):
        adapter = TelegramAdapter()
        status = await adapter.get_status("cmp_abc")
        assert status.campaign_id == "cmp_abc"
        assert status.channel == "telegram"
        assert status.status == "delivered"


# ---------------------------------------------------------------------------
# EmailPosterAdapter
# ---------------------------------------------------------------------------

class TestEmailPosterAdapter:
    def test_can_send_true(self):
        p = _player(email="ok@test.com", consent_marketing_email=True)
        c = _campaign()
        adapter = EmailPosterAdapter()
        assert adapter.can_send(p, c) is True

    def test_can_send_false_no_email(self):
        p = _player(email=None)
        c = _campaign()
        adapter = EmailPosterAdapter()
        assert adapter.can_send(p, c) is False

    def test_can_send_false_no_email_consent(self):
        p = _player(consent_marketing_email=False)
        c = _campaign()
        adapter = EmailPosterAdapter()
        assert adapter.can_send(p, c) is False

    @pytest.mark.asyncio
    async def test_send_returns_prepared(self):
        p = _player(email="ok@test.com")
        c = _campaign(campaign_id="cmp_e1")
        adapter = EmailPosterAdapter()
        result = await adapter.send(p, c)
        assert result.status == "prepared"
        assert result.channel == "email"
        assert result.recipient == "ok@test.com"

    @pytest.mark.asyncio
    async def test_send_blocked_returns_skipped(self):
        p = _player(email=None)
        c = _campaign()
        adapter = EmailPosterAdapter()
        result = await adapter.send(p, c)
        assert result.status == "skipped"
        assert "blocked" in (result.reason or "")

    @pytest.mark.asyncio
    async def test_get_status(self):
        adapter = EmailPosterAdapter()
        status = await adapter.get_status("cmp_e1")
        assert status.campaign_id == "cmp_e1"
        assert status.channel == "email"
        assert status.status == "prepared"


# ---------------------------------------------------------------------------
# LandingTrackingAdapter
# ---------------------------------------------------------------------------

class TestLandingTrackingAdapter:
    def test_link_for(self):
        adapter = LandingTrackingAdapter()
        url = adapter.link_for("cmp_abc")
        assert "/r/cmp_abc" in url

    def test_tracking_pixel_url(self):
        adapter = LandingTrackingAdapter()
        url = adapter.tracking_pixel_url("cmp_abc", "video_play")
        assert "/track/video_play" in url
        assert "campaign_id=cmp_abc" in url


# ---------------------------------------------------------------------------
# CrmWritebackAdapter
# ---------------------------------------------------------------------------

class TestCrmWritebackAdapter:
    def test_write_status(self):
        adapter = CrmWritebackAdapter()
        result = adapter.write_status("cmp_abc", "converted", channel="telegram")
        assert result["campaign_id"] == "cmp_abc"
        assert result["status"] == "converted"
        assert result["channel"] == "telegram"
        assert "written_at" in result

    def test_write_status_minimal(self):
        result = CrmWritebackAdapter.write_status("cmp_x", "failed")
        assert result["campaign_id"] == "cmp_x"
        assert result["status"] == "failed"
        assert "channel" not in result

    def test_write_delivery(self):
        result = CrmWritebackAdapter.write_delivery(
            "cmp_d", "telegram", "sent", recipient="12345"
        )
        assert result["campaign_id"] == "cmp_d"
        assert result["channel"] == "telegram"
        assert result["status"] == "sent"
        assert result["recipient"] == "12345"


# ---------------------------------------------------------------------------
# Protocol & dataclass smoke tests
# ---------------------------------------------------------------------------

class TestAdapterProtocol:
    def test_telegram_adapter_is_delivery_adapter(self):
        assert isinstance(TelegramAdapter(), DeliveryAdapter)

    def test_email_adapter_is_delivery_adapter(self):
        assert isinstance(EmailPosterAdapter(), DeliveryAdapter)


class TestDeliveryResult:
    def test_defaults(self):
        r = DeliveryResult(campaign_id="c", channel="telegram", status="sent")
        assert r.reason is None
        assert r.message_id is None

    def test_full_populated(self):
        r = DeliveryResult(
            campaign_id="c",
            channel="email",
            status="prepared",
            reason=None,
            message_id=None,
            recipient="a@b.com",
        )
        assert r.recipient == "a@b.com"


class TestDeliveryStatus:
    def test_defaults(self):
        s = DeliveryStatus(campaign_id="c", channel="telegram", status="delivered")
        assert s.sent_at is None
        assert s.failure_reason is None

    def test_full_populated(self):
        s = DeliveryStatus(
            campaign_id="c",
            channel="telegram",
            status="failed",
            failure_reason="timeout",
        )
        assert s.failure_reason == "timeout"

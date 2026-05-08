"""/delivery/send — orchestrate campaign delivery across available channels.

POST /delivery/send  {campaign_id: "cmp_001"}

TECH_SPEC §3.5 / T-24:
  - Load Campaign, Player, VideoAsset.
  - Validate readiness.
  - Check generation & delivery consent.
  - Select best channel; fallback to available if primary is blocked.
  - Call adapter(s) through injectable boundary.
  - Persist Delivery rows.
  - Call CrmWritebackAdapter after each attempt.
  - Return per-channel result summary.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.delivery.adapters import DeliveryAdapter, DeliveryResult
from app.delivery.crm_writeback import CrmWritebackAdapter
from app.delivery.eligibility import (
    block_reason,
    build_delivery_block_reason,
    can_send_channel,
    check_generation_consent,
    generation_block_reason,
    select_best_channel,
)
from app.delivery.email_adapter import EmailPosterAdapter
from app.delivery.telegram_adapter import TelegramAdapter
from app.db import get_session
from app.models import Campaign, CampaignStatus, Delivery, Player, VideoAsset

router = APIRouter()

# ── Pydantic schemas ────────────────────────────────────────────────────────


class SendRequest(BaseModel):
    campaign_id: str = Field(..., description="Campaign to deliver")


class ChannelSummary(BaseModel):
    channel: str
    status: str  # sent | prepared | skipped | failed
    reason: Optional[str] = None
    message_id: Optional[str] = None
    recipient: Optional[str] = None


class SendResponse(BaseModel):
    campaign_id: str
    overall_status: str  # sent | partial | blocked | failed
    channels: list[ChannelSummary]


# ── Adapter factories (injectable via dependency_overrides in tests) ────────


def _build_telegram() -> TelegramAdapter:
    return TelegramAdapter()


def _build_email() -> EmailPosterAdapter:
    return EmailPosterAdapter()


# ── Helpers ─────────────────────────────────────────────────────────────────


_MOCK_CHAT_ID_PREFIX = "mock_tg_"


def _is_mock_telegram_id(chat_id: Optional[str]) -> bool:
    """Return True if the chat_id is a non-numeric mock value that would break int()."""
    if not chat_id:
        return False
    if chat_id.startswith(_MOCK_CHAT_ID_PREFIX):
        return True
    try:
        int(chat_id)
        return False
    except (ValueError, TypeError):
        return True


def _persist_delivery(
    session: Session,
    campaign_id: str,
    channel: str,
    status: str,
    *,
    recipient: Optional[str] = None,
    failure_reason: Optional[str] = None,
    sent: bool = False,
) -> Delivery:
    row = Delivery(
        campaign_id=campaign_id,
        channel=channel,
        status=status,
        recipient=recipient,
        failure_reason=failure_reason,
        sent_at=datetime.now(timezone.utc) if sent else None,
    )
    session.add(row)
    return row


def _adapter_for_channel(
    channel: str,
    telegram: TelegramAdapter | None = None,
    email: EmailPosterAdapter | None = None,
) -> tuple[Optional[DeliveryAdapter], str | None]:
    """Return the adapter for a channel plus optional guard-persona identifier.

    For mock Telegram IDs we return (adapter, "mock_telegram_id_blocked")
    so the caller can skip real sends.
    """
    if channel == "telegram":
        return telegram, "telegram"
    if channel == "email":
        return email, "email"
    return None, None


# ══════════════════════════════════════════════════════════════════════════════
# POST /delivery/send
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/send", response_model=SendResponse)
async def send(
    body: SendRequest,
    session: Annotated[Session, Depends(get_session)],
    telegram: Annotated[TelegramAdapter, Depends(_build_telegram)] = None,  # type: ignore[assignment]
    email: Annotated[EmailPosterAdapter, Depends(_build_email)] = None,  # type: ignore[assignment]
) -> SendResponse:
    campaign = session.exec(
        select(Campaign).where(Campaign.campaign_id == body.campaign_id)
    ).first()
    if campaign is None:
        raise HTTPException(status_code=404, detail=f"Campaign {body.campaign_id!r} not found")

    # ── Readiness gate ────────────────────────────────────────────────────
    if campaign.status != CampaignStatus.ready:
        raise HTTPException(
            status_code=409,
            detail=f"Campaign must be in ready status to send (current: {campaign.status.value})",
        )

    # ── Load player & asset ───────────────────────────────────────────────
    player = session.exec(
        select(Player).where(Player.player_id == campaign.player_id)
    ).first()
    if player is None:
        raise HTTPException(status_code=404, detail=f"Player {campaign.player_id!r} not found")

    asset = session.exec(
        select(VideoAsset).where(VideoAsset.campaign_id == body.campaign_id)
    ).first()
    if asset is None or asset.status != "ready":
        raise HTTPException(
            status_code=409,
            detail="Campaign video asset must be ready before delivery",
        )

    # ── Generation consent gate ───────────────────────────────────────────
    if not check_generation_consent(player):
        reason = generation_block_reason(player) or "blocked_generation_consent"
        _persist_delivery(
            session,
            body.campaign_id,
            channel="",
            status="blocked",
            failure_reason=reason,
        )
        CrmWritebackAdapter.write_delivery(body.campaign_id, "", "blocked")
        session.commit()
        return SendResponse(
            campaign_id=body.campaign_id,
            overall_status="blocked",
            channels=[
                ChannelSummary(
                    channel="",
                    status="blocked",
                    reason=reason,
                )
            ],
        )

    # ── Channel selection ─────────────────────────────────────────────────
    best = select_best_channel(player, campaign)
    if best is None:
        block_reason_text = build_delivery_block_reason(player) or "blocked_no_reachable_channel"
        campaign.status = CampaignStatus.ready_blocked_delivery
        _persist_delivery(
            session,
            body.campaign_id,
            channel="",
            status="blocked",
            failure_reason=block_reason_text,
        )
        session.add(campaign)
        session.commit()
        return SendResponse(
            campaign_id=body.campaign_id,
            overall_status="blocked",
            channels=[
                ChannelSummary(
                    channel="",
                    status="skipped",
                    reason=block_reason_text,
                )
            ],
        )

    # ── Attempt delivery ──────────────────────────────────────────────────
    adapter, guard = _adapter_for_channel(best, telegram=telegram, email=email)
    if adapter is None:
        _persist_delivery(
            session,
            body.campaign_id,
            channel=best,
            status="skipped",
            failure_reason=f"no_adapter_for_{best}",
        )
        session.commit()
        return SendResponse(
            campaign_id=body.campaign_id,
            overall_status="blocked",
            channels=[
                ChannelSummary(
                    channel=best,
                    status="skipped",
                    reason=f"no_adapter_for_{best}",
                )
            ],
        )

    if not can_send_channel(player, best):
        skip_reason = block_reason(player, best) or f"blocked_{best}"
        _persist_delivery(
            session,
            body.campaign_id,
            channel=best,
            status="skipped",
            failure_reason=skip_reason,
        )
        CrmWritebackAdapter.write_delivery(
            body.campaign_id, best, "skipped", recipient=None
        )
        session.commit()
        return SendResponse(
            campaign_id=body.campaign_id,
            overall_status="blocked",
            channels=[
                ChannelSummary(
                    channel=best,
                    status="skipped",
                    reason=skip_reason,
                )
            ],
        )

    # Guard: mock Telegram IDs are not real — skip the real send call.
    if best == "telegram" and _is_mock_telegram_id(player.telegram_chat_id):
        _persist_delivery(
            session,
            body.campaign_id,
            channel="telegram",
            status="skipped",
            failure_reason="mock_telegram_chat_id_no_real_send",
            recipient=player.telegram_chat_id,
        )
        CrmWritebackAdapter.write_delivery(
            body.campaign_id, "telegram", "skipped", recipient=player.telegram_chat_id
        )
        session.commit()
        return SendResponse(
            campaign_id=body.campaign_id,
            overall_status="blocked",
            channels=[
                ChannelSummary(
                    channel="telegram",
                    status="skipped",
                    reason="mock_telegram_chat_id_no_real_send",
                    recipient=player.telegram_chat_id,
                )
            ],
        )

    # Real send attempt ────────────────────────────────────────────────────
    result: DeliveryResult = await adapter.send(player, campaign, asset)

    _persist_delivery(
        session,
        body.campaign_id,
        channel=result.channel,
        status=result.status,
        recipient=result.recipient,
        failure_reason=result.reason,
        sent=result.status in ("sent", "prepared"),
    )

    CrmWritebackAdapter.write_delivery(
        body.campaign_id,
        result.channel,
        result.status,
        recipient=result.recipient or None,
    )

    # ── Update campaign status ────────────────────────────────────────────
    if result.status == "sent":
        campaign.status = CampaignStatus.delivered
    elif result.status in ("prepared",):
        campaign.status = CampaignStatus.ready  # stays ready until "Mark as sent"
    else:
        campaign.status = CampaignStatus.ready_blocked_delivery

    campaign.updated_at = datetime.now(timezone.utc)
    session.add(campaign)
    session.commit()

    return SendResponse(
        campaign_id=body.campaign_id,
        overall_status=result.status,
        channels=[
            ChannelSummary(
                channel=result.channel,
                status=result.status,
                reason=result.reason,
                message_id=result.message_id,
                recipient=result.recipient,
            )
        ],
    )

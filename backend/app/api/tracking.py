"""Tracking webhook API.

POST /track/play     — video play/view event
POST /track/click    — CTA click event
POST /track/deposit  — mock deposit conversion

TECH_SPEC §3.5 / T-27:
  - Each endpoint persists a Tracking row.
  - click updates Delivery.clicked_at for matching campaign.
  - deposit sets Campaign.status = converted and calls CRM writeback.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.db import get_session
from app.models import Campaign, CampaignStatus, Delivery, Tracking

router = APIRouter()

# ── Pydantic schemas ────────────────────────────────────────────────────────


class PlayPayload(BaseModel):
    campaign_id: str = Field(..., description="Campaign being viewed")
    watched_seconds: Optional[int] = Field(None, ge=0, description="Seconds watched")


class ClickPayload(BaseModel):
    campaign_id: str = Field(..., description="Campaign the CTA belongs to")
    link_id: Optional[str] = Field(None, description="Which link was clicked")


class DepositPayload(BaseModel):
    campaign_id: str = Field(..., description="Campaign the deposit is attributed to")
    amount: float = Field(..., gt=0, description="Deposit amount")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code")


# ── Helpers ─────────────────────────────────────────────────────────────────


def _find_campaign(session: Session, campaign_id: str) -> Campaign:
    c = session.exec(select(Campaign).where(Campaign.campaign_id == campaign_id)).first()
    if c is None:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id!r} not found")
    return c  # type: ignore[return-value]


def _save_tracking(session: Session, campaign_id: str, event_type: str) -> Tracking:
    row = Tracking(campaign_id=campaign_id, event_type=event_type)
    session.add(row)
    return row


# ── POST /track/play ────────────────────────────────────────────────────────


@router.post("/play")
def track_play(
    body: PlayPayload,
    session: Annotated[Session, Depends(get_session)],
) -> dict:
    _find_campaign(session, body.campaign_id)
    _save_tracking(session, body.campaign_id, "video_play")
    session.commit()
    return {
        "campaign_id": body.campaign_id,
        "event_type": "video_play",
        "watched_seconds": body.watched_seconds,
        "status": "recorded",
    }


# ── POST /track/click ───────────────────────────────────────────────────────


@router.post("/click")
def track_click(
    body: ClickPayload,
    session: Annotated[Session, Depends(get_session)],
) -> dict:
    _find_campaign(session, body.campaign_id)
    _save_tracking(session, body.campaign_id, "cta_click")

    # Update any Delivery rows for this campaign with a click timestamp.
    deliveries = session.exec(
        select(Delivery).where(Delivery.campaign_id == body.campaign_id)
    ).all()
    now = datetime.now(timezone.utc)
    for d in deliveries:
        d.clicked_at = now
        session.add(d)

    session.commit()
    return {
        "campaign_id": body.campaign_id,
        "event_type": "cta_click",
        "link_id": body.link_id,
        "status": "recorded",
    }


# ── POST /track/deposit ─────────────────────────────────────────────────────


@router.post("/deposit")
def track_deposit(
    body: DepositPayload,
    session: Annotated[Session, Depends(get_session)],
) -> dict:
    campaign = _find_campaign(session, body.campaign_id)

    _save_tracking(session, body.campaign_id, "deposit_submit")

    # Update campaign status to converted.
    campaign.status = CampaignStatus.converted
    campaign.updated_at = datetime.now(timezone.utc)
    session.add(campaign)

    # Call mock CRM writeback.
    from app.delivery.crm_writeback import CrmWritebackAdapter

    CrmWritebackAdapter.write_status(
        body.campaign_id, status="converted"
    )

    session.commit()
    return {
        "campaign_id": body.campaign_id,
        "event_type": "deposit_submit",
        "amount": body.amount,
        "currency": body.currency,
        "status": "recorded",
    }

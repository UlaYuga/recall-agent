"""Approval API — CRM manager review gate.

GET  /approval/queue                     — pending campaigns with filters
POST /approval/{campaign_id}/approve     — approve → status = approved
POST /approval/{campaign_id}/reject      — reject with required reason
POST /approval/{campaign_id}/edit        — partial update of offer/script
POST /approval/{campaign_id}/regenerate-script — re-run script generator
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, or_, select

from app.agent.script_generator import generate_script
from app.db import get_session
from app.models import Campaign, CampaignStatus, Player

router = APIRouter()

# ── Pydantic request schemas ────────────────────────────────────────────────


class RejectBody(BaseModel):
    reason: str = Field(
        ...,
        min_length=1,
        description="Required reason: too_aggressive | wrong_offer | wrong_tone | data_issue | other",
    )


class EditBody(BaseModel):
    offer_json: Optional[str] = Field(None, description="Replacement Offer JSON string")
    script_json: Optional[str] = Field(None, description="Replacement Script JSON string")
    auto_approve: bool = Field(
        False, description="If true, approve immediately after edit"
    )


# ── Helpers ─────────────────────────────────────────────────────────────────


def _resolve_player(session: Session, player_id: str) -> Player:
    player = session.exec(select(Player).where(Player.player_id == player_id)).first()
    if player is None:
        raise HTTPException(status_code=404, detail=f"Player {player_id!r} not found")
    return player  # type: ignore[return-value]


def _get_campaign(session: Session, campaign_id: str) -> Campaign:
    campaign = session.exec(
        select(Campaign).where(Campaign.campaign_id == campaign_id)
    ).first()
    if campaign is None:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id!r} not found")
    return campaign  # type: ignore[return-value]


def _build_queue_item(campaign: Campaign, player: Player) -> dict[str, Any]:
    """Assemble a rich queue row with player profile + campaign fields."""
    return {
        "campaign_id": campaign.campaign_id,
        "player_id": campaign.player_id,
        "first_name": player.first_name,
        "country": player.country,
        "currency": player.currency,
        "cohort": campaign.cohort,
        "risk_score": campaign.risk_score,
        "status": campaign.status.value,
        "offer_json": campaign.offer_json,
        "script_json": campaign.script_json,
        "reasoning_json": campaign.reasoning_json,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
        # Lightweight player profile for the approval side-panel
        "player": {
            "first_name": player.first_name,
            "country": player.country,
            "currency": player.currency,
            "ltv_segment": player.ltv_segment,
            "last_login_at": player.last_login_at.isoformat() if player.last_login_at else None,
            "last_deposit_at": player.last_deposit_at.isoformat() if player.last_deposit_at else None,
            "total_deposits_count": player.total_deposits_count,
            "total_deposits_amount": player.total_deposits_amount,
            "favorite_vertical": player.favorite_vertical,
            "favorite_game_category": player.favorite_game_category,
            "favorite_game_label": player.favorite_game_label,
            "biggest_win_amount": player.biggest_win_amount,
            "biggest_win_currency": player.biggest_win_currency,
            "preferred_language": player.preferred_language,
        },
    }


def _merge_reject_reason(campaign: Campaign, reason: str) -> str:
    """Attach a reject reason to reasoning_json without destroying existing data.

    reasoning_json may be a JSON list (classifier output) or a dict (previously
    merged).  Normalise to a dict so reject_reason can be stored as a key.
    """
    try:
        raw = json.loads(campaign.reasoning_json or "{}")
        data: dict = raw if isinstance(raw, dict) else {}
    except (json.JSONDecodeError, TypeError):
        data = {}
    data["reject_reason"] = reason
    return json.dumps(data)


def _extract_offer_copy(campaign: Campaign) -> str:
    """Extract the offer copy text from campaign.offer_json, or return a safe default."""
    if not campaign.offer_json:
        return "your personal offer"
    try:
        offer_data = json.loads(campaign.offer_json)
        return str(offer_data.get("copy", offer_data.get("description", "your personal offer")))
    except (json.JSONDecodeError, TypeError):
        return "your personal offer"


def _touch(campaign: Campaign) -> None:
    campaign.updated_at = datetime.now(timezone.utc)


# ── GET /approval/queue ─────────────────────────────────────────────────────


@router.get("/queue")
def queue(
    cohort: Annotated[Optional[str], Query(description="Filter by cohort")] = None,
    risk_score_min: Annotated[
        Optional[float], Query(ge=0, le=100, description="Minimum risk score")
    ] = None,
    status: Annotated[
        Optional[CampaignStatus],
        Query(description="Filter by campaign status (default: draft + pending_approval)"),
    ] = None,
    session: Annotated[Session, Depends(get_session)] = None,
) -> list[dict[str, Any]]:
    """Return campaigns that are pending CRM manager review.

    By default returns campaigns in **draft** or **pending_approval** status.
    Filters narrow by cohort, minimum risk_score, or a specific status.
    Each row includes a lightweight player profile for the approval side-panel.
    """
    # Build base query — default to reviewable statuses.
    if status is not None:
        q = select(Campaign).where(Campaign.status == status)
    else:
        q = select(Campaign).where(
            or_(
                Campaign.status == CampaignStatus.draft,
                Campaign.status == CampaignStatus.pending_approval,
            )
        )

    if cohort:
        q = q.where(Campaign.cohort == cohort)
    if risk_score_min is not None:
        q = q.where(Campaign.risk_score >= risk_score_min)

    campaigns = session.exec(q.order_by(Campaign.created_at.desc())).all()

    items: list[dict[str, Any]] = []
    for c in campaigns:
        try:
            player = _resolve_player(session, c.player_id)
        except HTTPException:
            continue
        items.append(_build_queue_item(c, player))

    return items


# ── POST /approval/{campaign_id}/approve ────────────────────────────────────


@router.post("/{campaign_id}/approve")
def approve(
    campaign_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> dict[str, Any]:
    """Approve a campaign — status moves to **approved**."""
    campaign = _get_campaign(session, campaign_id)

    if campaign.status in (CampaignStatus.approved, CampaignStatus.delivered, CampaignStatus.converted):
        raise HTTPException(status_code=409, detail="Campaign is already approved or in a later stage")

    if campaign.status == CampaignStatus.rejected:
        raise HTTPException(status_code=409, detail="Cannot approve a rejected campaign — create a new one via /agent/scan")

    campaign.status = CampaignStatus.approved
    _touch(campaign)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    return {
        "campaign_id": campaign.campaign_id,
        "status": campaign.status.value,
        "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
    }


# ── POST /approval/{campaign_id}/reject ─────────────────────────────────────


@router.post("/{campaign_id}/reject")
def reject(
    campaign_id: str,
    body: RejectBody,
    session: Annotated[Session, Depends(get_session)],
) -> dict[str, Any]:
    """Reject a campaign with a required reason.

    Reason is stored in *reasoning_json* (merged with existing data).
    Status moves to **rejected**.
    """
    campaign = _get_campaign(session, campaign_id)

    if campaign.status == CampaignStatus.rejected:
        raise HTTPException(status_code=409, detail="Campaign is already rejected")

    if campaign.status in (CampaignStatus.delivered, CampaignStatus.converted):
        raise HTTPException(status_code=409, detail="Cannot reject a campaign that was already delivered")

    campaign.status = CampaignStatus.rejected
    campaign.reasoning_json = _merge_reject_reason(campaign, body.reason)
    _touch(campaign)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    return {
        "campaign_id": campaign.campaign_id,
        "status": campaign.status.value,
        "reject_reason": body.reason,
        "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
    }


# ── POST /approval/{campaign_id}/edit ───────────────────────────────────────


@router.post("/{campaign_id}/edit")
def edit(
    campaign_id: str,
    body: EditBody,
    session: Annotated[Session, Depends(get_session)],
) -> dict[str, Any]:
    """Edit a campaign's offer, script, or both.

    Optionally auto-approve after edit via *auto_approve*.
    Status must be **draft** or **pending_approval**.
    """
    campaign = _get_campaign(session, campaign_id)

    if campaign.status not in (CampaignStatus.draft, CampaignStatus.pending_approval):
        raise HTTPException(
            status_code=409,
            detail=f"Can only edit campaigns in draft or pending_approval status (current: {campaign.status.value})",
        )

    changed: list[str] = []
    if body.offer_json is not None:
        campaign.offer_json = body.offer_json
        changed.append("offer")
    if body.script_json is not None:
        campaign.script_json = body.script_json
        changed.append("script")

    if not changed:
        raise HTTPException(status_code=400, detail="No fields to edit — provide offer_json and/or script_json")

    if body.auto_approve:
        campaign.status = CampaignStatus.approved

    _touch(campaign)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    return {
        "campaign_id": campaign.campaign_id,
        "status": campaign.status.value,
        "changed": changed,
        "auto_approved": body.auto_approve,
        "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
    }


# ── POST /approval/{campaign_id}/regenerate-script ──────────────────────────


@router.post("/{campaign_id}/regenerate-script")
def regenerate_script(
    campaign_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> dict[str, Any]:
    """Re-run the script generator for this campaign's player + cohort + offer.

    The newly generated 4-scene script replaces *script_json*.
    Status must be **draft** or **pending_approval**.
    """
    campaign = _get_campaign(session, campaign_id)

    if campaign.status not in (CampaignStatus.draft, CampaignStatus.pending_approval):
        raise HTTPException(
            status_code=409,
            detail=f"Can only regenerate script for campaigns in draft or pending_approval status (current: {campaign.status.value})",
        )

    player = _resolve_player(session, campaign.player_id)
    offer_copy = _extract_offer_copy(campaign)

    script = generate_script(player, campaign.cohort, offer_copy)

    campaign.script_json = json.dumps(dict(script))
    _touch(campaign)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    return {
        "campaign_id": campaign.campaign_id,
        "script": script,
        "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
    }

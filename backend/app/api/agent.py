"""Agent API endpoints.

POST /agent/scan   — classify all players, create draft Campaign rows idempotently
GET  /agent/decide/{player_id} — full decision + 4-scene script for one player
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.agent.classifier import classify_player
from app.agent.offers import UnknownCohortError, select_offer
from app.agent.script_generator import generate_script
from app.db import get_session
from app.models import Campaign, CampaignStatus, Player
from app.workers.scheduler import _new_campaign_id, run_scan

router = APIRouter()

_TERMINAL: frozenset[CampaignStatus] = frozenset(
    {CampaignStatus.delivered, CampaignStatus.converted, CampaignStatus.rejected}
)


# ── POST /agent/scan ─────────────────────────────────────────────────────────


@router.post("/scan")
def scan(
    session: Annotated[Session, Depends(get_session)],
) -> dict[str, Any]:
    """Classify all players and create draft Campaign rows.

    Idempotent: players that already have a non-terminal campaign are skipped.
    """
    return run_scan(session)


# ── GET /agent/decide/{player_id} ────────────────────────────────────────────


@router.get("/decide/{player_id}")
def decide(
    player_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> dict[str, Any]:
    """Return cohort, risk_score, reasoning, offer, and 4-scene script.

    If the player has no active Campaign it is created on the fly.
    The generated script is persisted to Campaign.script_json.
    """
    player = session.exec(
        select(Player).where(Player.player_id == player_id)
    ).first()
    if player is None:
        raise HTTPException(status_code=404, detail=f"Player {player_id!r} not found")

    now = datetime.now(timezone.utc)
    result = classify_player(player, now=now)

    try:
        offer = select_offer(result.cohort, player)
    except UnknownCohortError:
        raise HTTPException(
            status_code=422,
            detail=f"No offer configured for cohort {result.cohort!r}",
        )

    # Find or create an active Campaign ──────────────────────────────────────
    all_campaigns = session.exec(
        select(Campaign).where(Campaign.player_id == player_id)
    ).all()
    active = [c for c in all_campaigns if c.status not in _TERMINAL]

    if active:
        campaign = active[0]
    else:
        campaign = Campaign(
            campaign_id=_new_campaign_id(),
            player_id=player.player_id,
            cohort=result.cohort,
            status=CampaignStatus.draft,
            risk_score=float(result.risk_score),
            reasoning_json=json.dumps(result.reasoning),
            offer_json=json.dumps(asdict(offer)),
        )
        session.add(campaign)

    # Generate script and persist ────────────────────────────────────────────
    script = generate_script(player, result.cohort, offer.copy)
    campaign.script_json = json.dumps(dict(script))
    campaign.updated_at = now
    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    return {
        "player_id": player_id,
        "campaign_id": campaign.campaign_id,
        "cohort": result.cohort,
        "risk_score": result.risk_score,
        "reasoning": result.reasoning,
        "offer": asdict(offer),
        "script": script,
    }

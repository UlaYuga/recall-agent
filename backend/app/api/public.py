"""Public read endpoints for the reactivation landing page.

GET /public/r/{campaign_id}  — minimal campaign card for the player-facing landing.

Intentionally exposes only:
  - campaign_id, status, cohort
  - first_name, preferred_language, currency
  - offer_json (structured offer copy shown to the player)
  - video_url / poster_url (from VideoAsset when ready)

Does NOT expose: player_id, financial details, internal pipeline metadata.
"""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models import Campaign, Player, VideoAsset

router = APIRouter()


class PublicCampaignCard(BaseModel):
    campaign_id: str
    status: str
    cohort: str
    first_name: str
    preferred_language: str
    currency: str
    offer_json: Optional[str] = None
    video_url: Optional[str] = None
    poster_url: Optional[str] = None


@router.get("/r/{campaign_id}", response_model=PublicCampaignCard)
def get_reactivation_card(
    campaign_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> PublicCampaignCard:
    """Return minimal campaign data for the public reactivation landing page.

    Returns 404 when the campaign or its player does not exist.
    Video URLs are null until the VideoAsset reaches ``ready`` status.
    """
    campaign = session.exec(
        select(Campaign).where(Campaign.campaign_id == campaign_id)
    ).first()
    if campaign is None:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id!r} not found")

    player = session.exec(
        select(Player).where(Player.player_id == campaign.player_id)
    ).first()
    if player is None:
        raise HTTPException(status_code=404, detail="Player for campaign not found")

    asset = session.exec(
        select(VideoAsset).where(VideoAsset.campaign_id == campaign_id)
    ).first()

    return PublicCampaignCard(
        campaign_id=campaign.campaign_id,
        status=campaign.status.value,
        cohort=campaign.cohort,
        first_name=player.first_name,
        preferred_language=player.preferred_language,
        currency=player.currency,
        offer_json=campaign.offer_json,
        video_url=asset.video_url if asset and asset.status == "ready" else None,
        poster_url=asset.poster_url if asset else None,
    )

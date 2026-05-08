"""Metrics dashboard endpoint.

GET /metrics/dashboard — aggregate KPIs, funnel counts, and cohort breakdown
read from live DB state. No writes; safe to call frequently.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import Campaign, CampaignStatus, Tracking

router = APIRouter()

_APPROVED_STATUSES: frozenset[CampaignStatus] = frozenset({
    CampaignStatus.approved,
    CampaignStatus.generating,
    CampaignStatus.generation_failed,
    CampaignStatus.ready,
    CampaignStatus.ready_blocked_delivery,
    CampaignStatus.delivered,
    CampaignStatus.converted,
})
_DELIVERED_STATUSES: frozenset[CampaignStatus] = frozenset({
    CampaignStatus.delivered,
    CampaignStatus.converted,
})


@router.get("/dashboard")
def metrics_dashboard(
    session: Annotated[Session, Depends(get_session)],
) -> dict:
    """Return aggregate KPIs, funnel, and cohort breakdown from live DB."""
    campaigns = session.exec(select(Campaign)).all()
    tracking_rows = session.exec(select(Tracking)).all()

    played_ids = {t.campaign_id for t in tracking_rows if t.event_type == "video_play"}
    clicked_ids = {t.campaign_id for t in tracking_rows if t.event_type == "cta_click"}

    scanned = len(campaigns)
    approved_n = sum(1 for c in campaigns if c.status in _APPROVED_STATUSES)
    delivered_n = sum(1 for c in campaigns if c.status in _DELIVERED_STATUSES)
    played = len(played_ids)
    clicked = len(clicked_ids)
    deposited = sum(1 for c in campaigns if c.status == CampaignStatus.converted)

    total_players = len({c.player_id for c in campaigns})
    approval_rate = approved_n / scanned if scanned else 0.0
    avg_ctr = clicked / played if played else 0.0
    reactivation_rate = deposited / delivered_n if delivered_n else 0.0

    cohort_data: dict[str, dict[str, int]] = defaultdict(
        lambda: {"count": 0, "approved": 0, "delivered": 0, "converted": 0}
    )
    for c in campaigns:
        cohort = c.cohort or "unknown"
        d = cohort_data[cohort]
        d["count"] += 1
        if c.status in _APPROVED_STATUSES:
            d["approved"] += 1
        if c.status in _DELIVERED_STATUSES:
            d["delivered"] += 1
        if c.status == CampaignStatus.converted:
            d["converted"] += 1

    cohort_breakdown = [{"cohort": k, **v} for k, v in sorted(cohort_data.items())]

    return {
        "funnel": {
            "scanned": scanned,
            "approved": approved_n,
            "delivered": delivered_n,
            "played": played,
            "clicked": clicked,
            "deposited": deposited,
        },
        "kpis": {
            "total_players": total_players,
            "campaigns_created": scanned,
            "approval_rate": round(approval_rate, 4),
            "videos_delivered": delivered_n,
            "avg_ctr": round(avg_ctr, 4),
            "reactivation_rate": round(reactivation_rate, 4),
        },
        "cohort_breakdown": cohort_breakdown,
    }

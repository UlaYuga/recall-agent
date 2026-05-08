"""Scan scheduler and manual trigger for the agent pipeline.

run_scan(session) is the shared helper used by both the hourly APScheduler
job and the POST /agent/scan API route.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, select

from app.agent.classifier import classify_player
from app.agent.offers import UnknownCohortError, select_offer
from app.db import get_session
from app.models import Campaign, CampaignStatus, Player

_TERMINAL: frozenset[CampaignStatus] = frozenset(
    {CampaignStatus.delivered, CampaignStatus.converted, CampaignStatus.rejected}
)

_scheduler: BackgroundScheduler | None = None


def _new_campaign_id() -> str:
    return f"c_{uuid.uuid4().hex}"


def run_scan(session: Session, now: datetime | None = None) -> dict[str, int]:
    """Classify all players and create draft Campaign rows — idempotent.

    Players that already have a non-terminal Campaign are skipped.
    Returns ``{"scanned": N, "created": N, "skipped": N}``.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    players = session.exec(select(Player)).all()

    created = 0
    skipped = 0

    for player in players:
        existing = session.exec(
            select(Campaign).where(Campaign.player_id == player.player_id)
        ).all()
        if any(c.status not in _TERMINAL for c in existing):
            skipped += 1
            continue

        result = classify_player(player, now=now)

        try:
            offer = select_offer(result.cohort, player)
        except UnknownCohortError:
            skipped += 1
            continue

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
        created += 1

    session.commit()
    return {"scanned": len(players), "created": created, "skipped": skipped}


def _scan_job() -> None:
    session = next(get_session())
    try:
        run_scan(session)
    finally:
        session.close()


def start_scheduler() -> None:
    """Start the hourly scan scheduler. Safe to call multiple times."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _scan_job, "interval", hours=1, id="hourly_scan", replace_existing=True
    )
    _scheduler.start()


def shutdown_scheduler() -> None:
    """Gracefully stop the scheduler."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


def trigger_manual_scan() -> dict[str, int]:
    """Run a scan immediately — useful for demo and ad-hoc triggering."""
    session = next(get_session())
    try:
        return run_scan(session)
    finally:
        session.close()


def scheduler_running() -> bool:
    """Return True if the APScheduler background thread is active."""
    return _scheduler is not None and _scheduler.running

"""Tests for the scan scheduler, manual trigger, and run_scan helper."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, select

from app.models import Campaign, CampaignStatus, Player
from app.workers import scheduler as scheduler_mod
from app.workers.scheduler import (
    _scan_job,
    _new_campaign_id,
    run_scan,
    scheduler_running,
    shutdown_scheduler,
    start_scheduler,
    trigger_manual_scan,
)

_NOW = datetime(2026, 5, 8, 12, 0, 0, tzinfo=timezone.utc)


def _make_player(
    player_id: str = "p_test",
    *,
    first_name: str = "Test",
    total_deposits_count: int = 5,
    total_deposits_amount: float = 1_000.0,
    last_login_at: datetime | None = None,
    last_deposit_at: datetime | None = None,
) -> Player:
    return Player(
        player_id=player_id,
        external_id=player_id,
        first_name=first_name,
        total_deposits_count=total_deposits_count,
        total_deposits_amount=total_deposits_amount,
        last_login_at=last_login_at or _NOW - timedelta(days=30),
        last_deposit_at=last_deposit_at or _NOW - timedelta(days=30),
    )


# ── Reset scheduler state between tests ──────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_scheduler() -> None:
    """Ensure the global scheduler is torn down before each test."""
    shutdown_scheduler()


# ── run_scan ──────────────────────────────────────────────────────────────────


class TestRunScan:
    def test_empty_db_returns_zeros(self, session: Session) -> None:
        result = run_scan(session, now=_NOW)
        assert result == {"scanned": 0, "created": 0, "skipped": 0}

    def test_creates_one_campaign_per_player(self, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.add(_make_player("p_002"))
        session.commit()

        result = run_scan(session, now=_NOW)
        assert result["scanned"] == 2
        assert result["created"] == 2
        assert result["skipped"] == 0

    def test_campaign_stored_in_db(self, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        run_scan(session, now=_NOW)

        session.expire_all()
        rows = session.exec(
            select(Campaign).where(Campaign.player_id == "p_001")
        ).all()
        assert len(rows) == 1

    def test_campaign_has_cohort(self, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        run_scan(session, now=_NOW)

        session.expire_all()
        c = session.exec(
            select(Campaign).where(Campaign.player_id == "p_001")
        ).first()
        assert c is not None and c.cohort

    def test_campaign_has_offer_json(self, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        run_scan(session, now=_NOW)

        session.expire_all()
        c = session.exec(
            select(Campaign).where(Campaign.player_id == "p_001")
        ).first()
        assert c is not None and c.offer_json is not None

    def test_campaign_has_reasoning_json(self, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        run_scan(session, now=_NOW)

        session.expire_all()
        c = session.exec(
            select(Campaign).where(Campaign.player_id == "p_001")
        ).first()
        assert c is not None and c.reasoning_json is not None

    def test_idempotent_second_scan_skips(self, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.commit()

        r1 = run_scan(session, now=_NOW)
        r2 = run_scan(session, now=_NOW)
        assert r1["created"] == 1
        assert r2["created"] == 0
        assert r2["skipped"] == 1

    def test_idempotent_no_duplicate_campaigns(self, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.commit()
        run_scan(session, now=_NOW)
        run_scan(session, now=_NOW)

        session.expire_all()
        rows = session.exec(
            select(Campaign).where(Campaign.player_id == "p_001")
        ).all()
        assert len(rows) == 1

    def test_new_campaign_after_terminal_status(self, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.commit()

        run_scan(session, now=_NOW)

        session.expire_all()
        c = session.exec(
            select(Campaign).where(Campaign.player_id == "p_001")
        ).first()
        assert c is not None
        c.status = CampaignStatus.delivered
        session.add(c)
        session.commit()

        r2 = run_scan(session, now=_NOW)
        assert r2["created"] == 1

    def test_campaign_ids_are_unique(self, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.add(_make_player("p_002"))
        session.commit()
        run_scan(session, now=_NOW)

        session.expire_all()
        campaigns = session.exec(select(Campaign)).all()
        ids = {c.campaign_id for c in campaigns}
        assert len(ids) == 2

    def test_all_campaigns_start_as_draft(self, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.add(_make_player("p_002"))
        session.commit()
        run_scan(session, now=_NOW)

        session.expire_all()
        for c in session.exec(select(Campaign)).all():
            assert c.status == CampaignStatus.draft

    def test_new_campaign_id_format(self) -> None:
        cid = _new_campaign_id()
        assert cid.startswith("c_")
        assert len(cid) > 2


# ── Scheduler lifecycle ──────────────────────────────────────────────────────


class TestSchedulerLifecycle:
    def test_start_creates_scheduler(self) -> None:
        with patch.object(scheduler_mod, "BackgroundScheduler") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.running = True
            mock_cls.return_value = mock_instance

            start_scheduler()

            mock_cls.assert_called_once()
            mock_instance.add_job.assert_called_once()
            job_args = mock_instance.add_job.call_args
            assert job_args[0][1] == "interval"
            assert job_args[1]["id"] == "hourly_scan"
            assert job_args[1]["hours"] == 1
            mock_instance.start.assert_called_once()

    def test_start_is_idempotent(self) -> None:
        with patch.object(scheduler_mod, "BackgroundScheduler") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.running = True
            mock_cls.return_value = mock_instance

            start_scheduler()
            start_scheduler()

            assert mock_cls.call_count == 1

    def test_shutdown_stops_running_scheduler(self) -> None:
        with patch.object(scheduler_mod, "BackgroundScheduler") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.running = True
            mock_cls.return_value = mock_instance
            start_scheduler()

            shutdown_scheduler()
            mock_instance.shutdown.assert_called_once_with(wait=False)

    def test_shutdown_is_idempotent(self) -> None:
        with patch.object(scheduler_mod, "BackgroundScheduler") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.running = True
            mock_cls.return_value = mock_instance
            start_scheduler()

            shutdown_scheduler()
            shutdown_scheduler()

            mock_instance.shutdown.assert_called_once_with(wait=False)

    def test_scheduler_running_true_after_start(self) -> None:
        with patch.object(scheduler_mod, "BackgroundScheduler") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.running = True
            mock_cls.return_value = mock_instance
            start_scheduler()

            assert scheduler_running() is True

    def test_scheduler_running_false_after_shutdown(self) -> None:
        with patch.object(scheduler_mod, "BackgroundScheduler") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.running = True
            mock_cls.return_value = mock_instance
            start_scheduler()
            shutdown_scheduler()

            assert scheduler_running() is False


# ── Manual trigger ────────────────────────────────────────────────────────────


class TestManualTrigger:
    def test_trigger_returns_counts(self, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.commit()

        with patch.object(scheduler_mod, "get_session") as mock_get:
            mock_get.return_value = iter([session])
            result = trigger_manual_scan()

        assert result["scanned"] == 1
        assert result["created"] == 1

    def test_trigger_creates_campaign(self, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.commit()

        with patch.object(scheduler_mod, "get_session") as mock_get:
            mock_get.return_value = iter([session])
            trigger_manual_scan()

        session.expire_all()
        rows = session.exec(
            select(Campaign).where(Campaign.player_id == "p_001")
        ).all()
        assert len(rows) == 1


# ── _scan_job helper ──────────────────────────────────────────────────────────


class TestScanJob:
    def test_scan_job_calls_run_scan(self, session: Session) -> None:
        session.add(_make_player("p_001"))
        session.commit()

        with patch.object(scheduler_mod, "get_session") as mock_get:
            mock_get.return_value = iter([session])
            _scan_job()

        session.expire_all()
        rows = session.exec(
            select(Campaign).where(Campaign.player_id == "p_001")
        ).all()
        assert len(rows) == 1

    def test_scan_job_closes_session_on_error(self) -> None:
        mock_session = MagicMock(spec=Session)
        mock_session.exec.side_effect = RuntimeError("DB error")

        with patch.object(scheduler_mod, "get_session") as mock_get:
            mock_get.return_value = iter([mock_session])
            with pytest.raises(RuntimeError, match="DB error"):
                _scan_job()

        mock_session.close.assert_called_once()

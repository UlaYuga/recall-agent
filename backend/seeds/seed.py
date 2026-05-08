import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import delete
from sqlmodel import Session

from app.db import engine, init_db
from app.models import Event, Player

SEEDS_DIR = Path(__file__).parent
DEFAULT_PLAYERS = SEEDS_DIR / "players.json"
DEFAULT_EVENTS = SEEDS_DIR / "events.json"


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_players(path: Path = DEFAULT_PLAYERS) -> list[Player]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    players: list[Player] = []
    for r in rows:
        bw = r.get("biggest_win") or {}
        ids = r.get("identifiers") or {}
        con = r.get("consent") or {}
        players.append(
            Player(
                player_id=r["player_id"],
                external_id=r["external_id"],
                first_name=r["first_name"],
                preferred_language=r.get("preferred_language", "en"),
                market_language=r.get("market_language", ""),
                country=r.get("country", ""),
                currency=r.get("currency", ""),
                registered_at=_parse_dt(r.get("registered_at")),
                last_login_at=_parse_dt(r.get("last_login_at")),
                last_deposit_at=_parse_dt(r.get("last_deposit_at")),
                total_deposits_count=r.get("total_deposits_count", 0),
                total_deposits_amount=float(r.get("total_deposits_amount", 0)),
                favorite_vertical=r.get("favorite_vertical"),
                favorite_game_category=r.get("favorite_game_category"),
                favorite_game_label=r.get("favorite_game_label"),
                biggest_win_amount=bw.get("amount"),
                biggest_win_currency=bw.get("currency"),
                biggest_win_at=_parse_dt(bw.get("at")),
                ltv_segment=r.get("ltv_segment", ""),
                tags=json.dumps(r.get("tags") or []),
                preferred_channels=json.dumps(r.get("preferred_channels") or []),
                external_crm_id=ids.get("external_crm_id"),
                email=ids.get("email"),
                phone_e164=ids.get("phone_e164"),
                telegram_chat_id=ids.get("telegram_chat_id"),
                push_token=ids.get("push_token"),
                consent_marketing_communications=bool(con.get("marketing_communications")),
                consent_marketing_email=bool(con.get("marketing_email")),
                consent_marketing_sms=bool(con.get("marketing_sms")),
                consent_whatsapp_business=bool(con.get("whatsapp_business")),
                consent_push_notifications=bool(con.get("push_notifications")),
                consent_video_personalization=bool(con.get("video_personalization")),
                consent_data_processing=bool(con.get("data_processing")),
            )
        )
    return players


def load_events(path: Path = DEFAULT_EVENTS) -> list[Event]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    events: list[Event] = []
    for r in rows:
        events.append(
            Event(
                event_id=r["event_id"],
                player_id=r["player_id"],
                event_type=r["event_type"],
                event_at=_parse_dt(r["event_at"]),  # type: ignore[arg-type]
                vertical=r.get("vertical"),
                game_category=r.get("game_category"),
                game_label=r.get("game_label"),
                amount=r.get("amount"),
                currency=r.get("currency"),
                metadata_json=json.dumps(r.get("metadata") or {}),
            )
        )
    return events


def seed_database(
    session: Session,
    players_path: Path = DEFAULT_PLAYERS,
    events_path: Path = DEFAULT_EVENTS,
) -> dict[str, int]:
    """Wipe Player+Event tables and reload from seed JSON. Idempotent.

    Does NOT touch Campaign, VideoAsset, Delivery, Tracking, or RunwayTask.
    """
    session.execute(delete(Event))
    session.execute(delete(Player))
    session.commit()

    players = load_players(players_path)
    events = load_events(events_path)

    for p in players:
        session.add(p)
    for e in events:
        session.add(e)
    session.commit()

    return {"players": len(players), "events": len(events)}


def main() -> None:
    init_db()
    with Session(engine) as session:
        counts = seed_database(session)
    print(f"Seeded {counts['players']} players and {counts['events']} events.")


if __name__ == "__main__":
    main()

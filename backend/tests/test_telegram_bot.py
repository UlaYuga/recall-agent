from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

import app.models  # noqa: F401
from app.models import Player
from app.telegram.bot import (
    _find_player_by_chat_id,
    _resolve_player_by_code,
    build_bot,
    build_dispatcher,
    help_command,
    optin_command,
    optout_command,
    save_player_chat_id,
    set_player_telegram_optin,
    start_command,
)
from app.telegram import bot as bot_module


@pytest.fixture()
def mem_session() -> Session:
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(eng)
    with Session(eng) as session:
        yield session
    eng.dispose()


def _seed_player(session: Session, player_id: str = "p_test", **kwargs) -> Player:
    p = Player(
        player_id=player_id,
        external_id=kwargs.get("external_id", f"ext_{player_id}"),
        first_name=kwargs.get("first_name", "Test"),
        telegram_chat_id=kwargs.get("telegram_chat_id", None),
        consent_marketing_communications=kwargs.get("consent_marketing_communications", False),
    )
    session.add(p)
    session.commit()
    return p


def make_message(chat_id: int = 123456, text: str = "/start"):
    msg = MagicMock()
    msg.chat.id = chat_id
    msg.text = text
    msg.from_user = MagicMock()
    msg.from_user.username = None
    msg.answer = AsyncMock()
    return msg


# ── Helper tests (real SQLite) ──────────────────────────────────────────────


def test_save_player_chat_id_updates_record(mem_session: Session) -> None:
    _seed_player(mem_session, player_id="p_001", telegram_chat_id=None)

    result = save_player_chat_id(mem_session, "p_001", 999888)
    assert result is not None
    assert result.telegram_chat_id == "999888"

    reloaded = mem_session.exec(
        select(Player).where(Player.player_id == "p_001")
    ).first()
    assert reloaded is not None
    assert reloaded.telegram_chat_id == "999888"


def test_save_player_chat_id_unknown_player(mem_session: Session) -> None:
    result = save_player_chat_id(mem_session, "nonexistent", 123)
    assert result is None


def test_set_player_telegram_optin_true(mem_session: Session) -> None:
    _seed_player(mem_session, player_id="p_001", telegram_chat_id="111", consent_marketing_communications=False)
    assert set_player_telegram_optin(mem_session, 111, True)

    reloaded = mem_session.exec(
        select(Player).where(Player.player_id == "p_001")
    ).first()
    assert reloaded is not None
    assert reloaded.consent_marketing_communications is True


def test_set_player_telegram_optin_false(mem_session: Session) -> None:
    _seed_player(mem_session, player_id="p_001", telegram_chat_id="111", consent_marketing_communications=True)
    assert set_player_telegram_optin(mem_session, 111, False)

    reloaded = mem_session.exec(
        select(Player).where(Player.player_id == "p_001")
    ).first()
    assert reloaded is not None
    assert reloaded.consent_marketing_communications is False


def test_set_player_telegram_optin_unknown_chat(mem_session: Session) -> None:
    assert set_player_telegram_optin(mem_session, 999, True) is False


def test_find_player_by_chat_id_found(mem_session: Session) -> None:
    _seed_player(mem_session, player_id="p_001", telegram_chat_id="111")
    result = _find_player_by_chat_id(mem_session, 111)
    assert result is not None
    assert result.player_id == "p_001"


def test_find_player_by_chat_id_not_found(mem_session: Session) -> None:
    result = _find_player_by_chat_id(mem_session, 999)
    assert result is None


def test_resolve_player_by_code_player_id(mem_session: Session) -> None:
    _seed_player(mem_session, player_id="p_001", external_id="ext_001")
    result = _resolve_player_by_code(mem_session, "p_001")
    assert result is not None
    assert result.player_id == "p_001"


def test_resolve_player_by_code_external_id(mem_session: Session) -> None:
    _seed_player(mem_session, player_id="p_001", external_id="ext_001")
    result = _resolve_player_by_code(mem_session, "ext_001")
    assert result is not None
    assert result.player_id == "p_001"


def test_resolve_player_by_code_not_found(mem_session: Session) -> None:
    result = _resolve_player_by_code(mem_session, "unknown")
    assert result is None


# ── Factory tests ────────────────────────────────────────────────────────────


def test_build_bot_with_explicit_token() -> None:
    bot = build_bot(token="123:abc")
    assert bot is not None


def test_build_bot_raises_on_placeholder() -> None:
    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
        build_bot(token="replace_me")


def test_build_bot_raises_on_empty_string() -> None:
    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
        build_bot(token="")


def test_build_bot_uses_settings_when_no_token() -> None:
    with patch.object(bot_module, "settings") as mock_settings:
        mock_settings.telegram_bot_token = "123456:ABC-DEF1234ghijkl"
        bot = build_bot()
        assert bot is not None


def test_build_dispatcher_registers_commands() -> None:
    dp = build_dispatcher()
    assert dp is not None
    registered = {str(h.callback.__name__) for h in dp.message.handlers if hasattr(h, "callback")}
    expected = {"start_command", "optin_command", "optout_command", "help_command"}
    assert expected.issubset(registered)


# ── Command handler tests (mocked) ──────────────────────────────────────────


def test_start_command_with_valid_code(mem_session: Session) -> None:
    _seed_player(mem_session, player_id="p_001", telegram_chat_id=None, first_name="Lucas")
    msg = make_message(text="/start p_001")

    with patch("app.telegram.bot.get_session") as mock_get:
        mock_get.return_value = iter([mem_session])

        import asyncio
        asyncio.run(start_command(msg))

    msg.answer.assert_awaited_once()
    answer_text = msg.answer.call_args[0][0]
    assert "Lucas" in answer_text
    assert "linked" in answer_text


def test_start_command_with_unknown_code(mem_session: Session) -> None:
    msg = make_message(text="/start unknown_code")

    with patch("app.telegram.bot.get_session") as mock_get:
        mock_get.return_value = iter([mem_session])

        import asyncio
        asyncio.run(start_command(msg))

    msg.answer.assert_awaited_once()
    answer_text = msg.answer.call_args[0][0]
    assert "Welcome to Recall" in answer_text


def test_start_command_no_code(mem_session: Session) -> None:
    msg = make_message(text="/start")

    with patch("app.telegram.bot.get_session") as mock_get:
        mock_session = MagicMock(spec=Session)
        mock_get.return_value = iter([mock_session])

        import asyncio
        asyncio.run(start_command(msg))

    msg.answer.assert_awaited_once()
    answer_text = msg.answer.call_args[0][0]
    assert "Welcome to Recall" in answer_text


def test_optin_command_registered_player(mem_session: Session) -> None:
    _seed_player(mem_session, player_id="p_001", telegram_chat_id="777", consent_marketing_communications=False)
    msg = make_message(chat_id=777, text="/optin")

    with patch("app.telegram.bot.get_session") as mock_get:
        mock_get.return_value = iter([mem_session])

        import asyncio
        asyncio.run(optin_command(msg))

    msg.answer.assert_awaited_once()
    answer_text = msg.answer.call_args[0][0]
    assert "opted in" in answer_text

    reloaded = mem_session.exec(
        select(Player).where(Player.player_id == "p_001")
    ).first()
    assert reloaded is not None
    assert reloaded.consent_marketing_communications is True


def test_optin_command_unregistered_player(mem_session: Session) -> None:
    msg = make_message(chat_id=999, text="/optin")

    with patch("app.telegram.bot.get_session") as mock_get:
        mock_get.return_value = iter([mem_session])

        import asyncio
        asyncio.run(optin_command(msg))

    msg.answer.assert_awaited_once()
    answer_text = msg.answer.call_args[0][0]
    assert "not registered" in answer_text.lower()


def test_optout_command_registered_player(mem_session: Session) -> None:
    _seed_player(mem_session, player_id="p_001", telegram_chat_id="777", consent_marketing_communications=True)
    msg = make_message(chat_id=777, text="/optout")

    with patch("app.telegram.bot.get_session") as mock_get:
        mock_get.return_value = iter([mem_session])

        import asyncio
        asyncio.run(optout_command(msg))

    msg.answer.assert_awaited_once()
    answer_text = msg.answer.call_args[0][0]
    assert "opted out" in answer_text

    reloaded = mem_session.exec(
        select(Player).where(Player.player_id == "p_001")
    ).first()
    assert reloaded is not None
    assert reloaded.consent_marketing_communications is False


def test_optout_command_unregistered_player(mem_session: Session) -> None:
    msg = make_message(chat_id=999, text="/optout")

    with patch("app.telegram.bot.get_session") as mock_get:
        mock_get.return_value = iter([mem_session])

        import asyncio
        asyncio.run(optout_command(msg))

    msg.answer.assert_awaited_once()
    answer_text = msg.answer.call_args[0][0]
    assert "not registered" in answer_text.lower()


def test_help_command() -> None:
    msg = make_message(text="/help")

    import asyncio
    asyncio.run(help_command(msg))

    msg.answer.assert_awaited_once()
    answer_text = msg.answer.call_args[0][0]
    assert "/start" in answer_text
    assert "/optin" in answer_text
    assert "/optout" in answer_text
    assert "/help" in answer_text


# ── Module import safety ─────────────────────────────────────────────────────


def test_module_imports_without_token() -> None:
    """Module must import successfully even if TELEGRAM_BOT_TOKEN is unset."""
    import importlib

    import app.telegram.bot as bot_module
    importlib.reload(bot_module)
    assert hasattr(bot_module, "build_bot")

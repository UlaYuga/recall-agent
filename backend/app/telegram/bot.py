from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from sqlmodel import Session, select

from app.config import settings
from app.db import get_session
from app.models import Player


def _find_player_by_chat_id(session: Session, chat_id: int) -> Player | None:
    return session.exec(
        select(Player).where(Player.telegram_chat_id == str(chat_id))
    ).first()


def _resolve_player_by_code(session: Session, code: str) -> Player | None:
    return session.exec(
        select(Player).where((Player.player_id == code) | (Player.external_id == code))
    ).first()


def save_player_chat_id(session: Session, player_id: str, chat_id: int) -> Player | None:
    player = session.exec(select(Player).where(Player.player_id == player_id)).first()
    if player is None:
        return None
    player.telegram_chat_id = str(chat_id)
    session.add(player)
    session.commit()
    return player


def set_player_telegram_optin(session: Session, chat_id: int, opted_in: bool) -> bool:
    player = _find_player_by_chat_id(session, chat_id)
    if player is None:
        return False
    player.consent_marketing_communications = opted_in
    session.add(player)
    session.commit()
    return True


async def start_command(message: Message) -> None:
    chat_id = message.chat.id
    args = message.text.split() if message.text else []
    code = args[1] if len(args) > 1 else None

    session = next(get_session())
    try:
        if code:
            player = _resolve_player_by_code(session, code)
            if player is not None:
                save_player_chat_id(session, player.player_id, chat_id)
                await message.answer(
                    f"Welcome, {player.first_name}! Your Telegram is now linked. "
                    "Use /optin to receive videos or /optout to stop."
                )
                return

        await message.answer(
            "Welcome to Recall! Use /optin to receive personalized video updates, "
            "or /optout to stop. Use /help to see all commands."
        )
    finally:
        session.close()


async def optin_command(message: Message) -> None:
    chat_id = message.chat.id
    session = next(get_session())
    try:
        player = _find_player_by_chat_id(session, chat_id)
        if player is not None:
            set_player_telegram_optin(session, chat_id, True)
            await message.answer("You are now opted in to receive video updates.")
        else:
            await message.answer(
                "You are not registered yet. Use /start <code> with your reactivation code."
            )
    finally:
        session.close()


async def optout_command(message: Message) -> None:
    chat_id = message.chat.id
    session = next(get_session())
    try:
        player = _find_player_by_chat_id(session, chat_id)
        if player is not None:
            set_player_telegram_optin(session, chat_id, False)
            await message.answer("You have opted out. No further messages will be sent.")
        else:
            await message.answer("You are not registered. No action needed.")
    finally:
        session.close()


async def help_command(message: Message) -> None:
    await message.answer(
        "/start [code] — Link your account\n"
        "/optin — Receive video updates\n"
        "/optout — Stop receiving updates\n"
        "/help — Show this help"
    )


def build_bot(token: str | None = None) -> Bot:
    if token is None:
        token = settings.telegram_bot_token
    if not token or token == "replace_me":
        raise ValueError("TELEGRAM_BOT_TOKEN is not set or still has the placeholder value")
    return Bot(token=token)


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.message.register(start_command, Command("start"))
    dp.message.register(optin_command, Command("optin"))
    dp.message.register(optout_command, Command("optout"))
    dp.message.register(help_command, Command("help"))
    return dp


async def start_polling(bot: Bot | None = None) -> None:
    if bot is None:
        bot = build_bot()
    dp = build_dispatcher()
    await dp.start_polling(bot)

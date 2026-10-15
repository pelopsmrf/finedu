"""Minimal long-polling Telegram bot handling /start and /delete_my_data.

Run as a standalone process (see deploy/finedu-bot.service):
    python -m app.scripts.bot
"""

import logging
import sqlite3
import time

import httpx

from app.config import Settings, get_settings
from app.db import delete_user_data, get_connection, init_db
from app.notifications import open_app_markup, send_message

START_TEXT = (
    "Привет! 👋 Finedu — короткие уроки и квизы про деньги: бюджет, накопления, "
    "кредиты. Жми кнопку ниже, чтобы начать 📘"
)
DELETE_CONFIRMATION_TEXT = "Твои данные удалены. Будем рады видеть тебя снова! 👋"

log = logging.getLogger("finedu.bot")


def handle_start(
    conn: sqlite3.Connection, chat_id: int, bot_token: str, sender=None, webapp_url: str = ""
) -> None:
    markup = open_app_markup(webapp_url) if webapp_url else None
    send_message(bot_token, chat_id, START_TEXT, sender=sender, reply_markup=markup)


def handle_delete_my_data(
    conn: sqlite3.Connection, chat_id: int, bot_token: str, sender=None
) -> None:
    delete_user_data(conn, chat_id)
    send_message(bot_token, chat_id, DELETE_CONFIRMATION_TEXT, sender=sender)


def dispatch(conn: sqlite3.Connection, settings: Settings, update: dict, sender=None) -> None:
    message = update.get("message") or {}
    text = (message.get("text") or "").strip()
    chat = message.get("chat", {})
    # Only private chats: there chat.id equals the user's telegram_id.
    if chat.get("id") is None or chat.get("type", "private") != "private":
        return
    chat_id = chat["id"]
    # "/start abc" (deep link) and "/start@finedu_bot" are still /start.
    command = text.split(maxsplit=1)[0].split("@")[0] if text else ""
    if command == "/start":
        handle_start(conn, chat_id, settings.bot_token, sender=sender, webapp_url=settings.webapp_url)
    elif command == "/delete_my_data":
        handle_delete_my_data(conn, chat_id, settings.bot_token, sender=sender)


def poll_forever() -> None:  # pragma: no cover - requires live network, not unit tested
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    conn = get_connection(settings.db_path)
    init_db(conn)
    offset = 0
    while True:
        try:
            resp = httpx.get(
                f"https://api.telegram.org/bot{settings.bot_token}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35,
            )
            updates = resp.json().get("result", [])
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("getUpdates failed: %s; retrying in 5 s", exc)
            time.sleep(5)
            continue
        for update in updates:
            offset = update["update_id"] + 1
            try:
                dispatch(conn, settings, update)
            except Exception:  # one bad update must not stop the bot
                log.exception("Failed to handle update %s", update.get("update_id"))
        time.sleep(1)


if __name__ == "__main__":  # pragma: no cover
    poll_forever()

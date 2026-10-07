"""Minimal long-polling Telegram bot handling /start and /delete_my_data.

Run as a standalone process (see deploy/finedu-bot.service):
    python -m app.scripts.bot
"""

import sqlite3
import time

import httpx

from app.config import Settings, get_settings
from app.db import delete_user_data, get_connection, init_db
from app.notifications import send_message

START_TEXT = "Привет! Открой Finedu через кнопку меню, чтобы начать учиться 📘"
DELETE_CONFIRMATION_TEXT = "Твои данные удалены. Будем рады видеть тебя снова! 👋"


def handle_start(conn: sqlite3.Connection, chat_id: int, bot_token: str, sender=None) -> None:
    send_message(bot_token, chat_id, START_TEXT, sender=sender)


def handle_delete_my_data(
    conn: sqlite3.Connection, chat_id: int, bot_token: str, sender=None
) -> None:
    delete_user_data(conn, chat_id)
    send_message(bot_token, chat_id, DELETE_CONFIRMATION_TEXT, sender=sender)


def dispatch(conn: sqlite3.Connection, settings: Settings, update: dict) -> None:
    message = update.get("message") or {}
    text = (message.get("text") or "").strip()
    chat_id = message.get("chat", {}).get("id")
    if chat_id is None:
        return
    if text == "/start":
        handle_start(conn, chat_id, settings.bot_token)
    elif text == "/delete_my_data":
        handle_delete_my_data(conn, chat_id, settings.bot_token)


def poll_forever() -> None:  # pragma: no cover - requires live network, not unit tested
    settings = get_settings()
    conn = get_connection(settings.db_path)
    init_db(conn)
    offset = 0
    while True:
        resp = httpx.get(
            f"https://api.telegram.org/bot{settings.bot_token}/getUpdates",
            params={"offset": offset, "timeout": 30},
            timeout=35,
        )
        for update in resp.json().get("result", []):
            offset = update["update_id"] + 1
            dispatch(conn, settings, update)
        time.sleep(1)


if __name__ == "__main__":  # pragma: no cover
    poll_forever()

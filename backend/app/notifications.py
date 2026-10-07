import sqlite3
from datetime import datetime, timedelta, timezone

import httpx

from app.config import Settings

REMINDER_TEXT = (
    "Продолжи обучение в Finedu — осталось совсем немного, чтобы завершить тему! 🚀"
)


def find_inactive_users(conn: sqlite3.Connection, days: int) -> list[int]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows = conn.execute(
        "SELECT u.telegram_id AS telegram_id, "
        "COALESCE(MAX(p.last_activity_at), u.created_at) AS last_activity "
        "FROM users u LEFT JOIN progress p ON p.telegram_id = u.telegram_id "
        "GROUP BY u.telegram_id "
        "HAVING last_activity < ?",
        (cutoff,),
    ).fetchall()
    return [r["telegram_id"] for r in rows]


def send_message(
    bot_token: str, chat_id: int, text: str, sender=None
) -> bool:
    sender = sender or httpx.post
    try:
        resp = sender(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except httpx.HTTPError:
        return False
    return resp.status_code == 200


def send_reminders(conn: sqlite3.Connection, settings: Settings, sender=None) -> int:
    inactive = find_inactive_users(conn, settings.reminder_days)
    sent = 0
    for telegram_id in inactive:
        if send_message(settings.bot_token, telegram_id, REMINDER_TEXT, sender=sender):
            sent += 1
    return sent


def broadcast(
    conn: sqlite3.Connection,
    settings: Settings,
    text: str,
    only_inactive_days: int | None = None,
    sender=None,
) -> int:
    if only_inactive_days is not None:
        targets = find_inactive_users(conn, only_inactive_days)
    else:
        targets = [r["telegram_id"] for r in conn.execute("SELECT telegram_id FROM users")]
    sent = 0
    for telegram_id in targets:
        if send_message(settings.bot_token, telegram_id, text, sender=sender):
            sent += 1
    return sent

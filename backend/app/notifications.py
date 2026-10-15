import sqlite3
from datetime import datetime, timedelta, timezone

import httpx

from app.config import Settings

REMINDER_TEXT = (
    "Продолжи обучение в Finedu — осталось совсем немного, чтобы завершить тему! 🚀"
)
REMINDER_WITH_LESSON_TEXT = "Давно не виделись! 👋 Тебя ждёт урок «{title}» — это займёт пару минут. 🚀"
OPEN_APP_TEXT = "Открыть Finedu"
CONTINUE_TEXT = "Продолжить урок"

# Last activity per user: latest progress row, or the user's creation date if there is none.
_LAST_ACTIVITY = (
    "SELECT u.telegram_id AS telegram_id, u.last_reminded_at AS last_reminded_at, "
    "COALESCE(MAX(p.last_activity_at), u.created_at) AS last_activity "
    "FROM users u LEFT JOIN progress p ON p.telegram_id = u.telegram_id "
    "WHERE u.notifications_enabled = 1 "
    "GROUP BY u.telegram_id "
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def find_inactive_users(conn: sqlite3.Connection, days: int) -> list[int]:
    """Users with notifications on who have been inactive for more than `days` days."""
    cutoff = (_now() - timedelta(days=days)).isoformat()
    rows = conn.execute(_LAST_ACTIVITY + "HAVING last_activity < ?", (cutoff,)).fetchall()
    return [r["telegram_id"] for r in rows]


def find_users_to_remind(conn: sqlite3.Connection, days: int) -> list[int]:
    """Inactive users who have not been reminded since their last activity.

    One reminder per pause: if the user ignores it, they are not messaged again
    until they come back to the app and then go quiet once more.
    """
    cutoff = (_now() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        _LAST_ACTIVITY
        + "HAVING last_activity < ? AND (last_reminded_at IS NULL OR last_reminded_at < last_activity)",
        (cutoff,),
    ).fetchall()
    return [r["telegram_id"] for r in rows]


def next_lesson_for(conn: sqlite3.Connection, telegram_id: int) -> sqlite3.Row | None:
    """First unfinished visible lesson, preferring topics the user has already started."""
    return conn.execute(
        "SELECT l.id AS id, l.title AS title FROM lessons l "
        "JOIN topics t ON t.id = l.topic_id "
        "WHERE l.is_published = 1 AND t.is_published = 1 "
        "AND l.id NOT IN (SELECT lesson_id FROM progress WHERE telegram_id = ? "
        "  AND lesson_id IS NOT NULL AND completed_at IS NOT NULL) "
        "ORDER BY t.id NOT IN (SELECT l2.topic_id FROM progress p "
        "  JOIN lessons l2 ON l2.id = p.lesson_id WHERE p.telegram_id = ?), "
        't."order", t.id, l."order", l.id LIMIT 1',
        (telegram_id, telegram_id),
    ).fetchone()


def open_app_markup(url: str, text: str = OPEN_APP_TEXT) -> dict:
    """Inline keyboard with one button that opens the Mini App at `url`."""
    return {"inline_keyboard": [[{"text": text, "web_app": {"url": url}}]]}


def send_message(
    bot_token: str, chat_id: int, text: str, sender=None, reply_markup: dict | None = None
) -> bool:
    sender = sender or httpx.post
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    try:
        resp = sender(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json=payload,
            timeout=10,
        )
    except httpx.HTTPError:
        return False
    return resp.status_code == 200


def send_reminders(conn: sqlite3.Connection, settings: Settings, sender=None) -> int:
    sent = 0
    for telegram_id in find_users_to_remind(conn, settings.reminder_days):
        lesson = next_lesson_for(conn, telegram_id)
        if lesson is not None:
            text = REMINDER_WITH_LESSON_TEXT.format(title=lesson["title"])
            markup = open_app_markup(f"{settings.webapp_url}/lessons/{lesson['id']}", CONTINUE_TEXT)
        else:
            text = REMINDER_TEXT
            markup = open_app_markup(settings.webapp_url)
        if send_message(settings.bot_token, telegram_id, text, sender=sender, reply_markup=markup):
            conn.execute(
                "UPDATE users SET last_reminded_at = ? WHERE telegram_id = ?",
                (_now().isoformat(), telegram_id),
            )
            conn.commit()
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
        targets = [
            r["telegram_id"]
            for r in conn.execute("SELECT telegram_id FROM users WHERE notifications_enabled = 1")
        ]
    markup = open_app_markup(settings.webapp_url)
    sent = 0
    for telegram_id in targets:
        if send_message(settings.bot_token, telegram_id, text, sender=sender, reply_markup=markup):
            sent += 1
    return sent

"""Notification switch, one reminder per pause, reminder points at the next lesson, bot /start."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.db import ensure_user, get_connection, get_db, init_db, set_notifications
from app.main import app

TEST_BOT_TOKEN = "test-bot-token"  # noqa: S105 - test fixture only


class FakeSender:
    def __init__(self):
        self.calls = []

    def __call__(self, url, json=None, timeout=10):
        self.calls.append((url, json))

        class Resp:
            status_code = 200

        return Resp()


def _settings():
    return Settings(
        bot_token=TEST_BOT_TOKEN, admin_id=1, db_path=":memory:", webapp_url="https://example.test"
    )


@pytest.fixture
def conn(tmp_path):
    c = get_connection(str(tmp_path / "n.db"))
    init_db(c)
    yield c
    c.close()


def _inactive_user(conn, telegram_id, days=10):
    ts = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    ensure_user(conn, telegram_id, ts)
    conn.execute(
        "INSERT INTO progress (telegram_id, last_activity_at) VALUES (?, ?)", (telegram_id, ts)
    )
    conn.commit()


def _lesson(conn, title, topic_order=0, lesson_order=0):
    cur = conn.execute(
        'INSERT INTO topics (title, "order", is_published) VALUES (?, ?, 1)', (title, topic_order)
    )
    lid = conn.execute(
        'INSERT INTO lessons (topic_id, title, "order", is_published) VALUES (?, ?, ?, 1)',
        (cur.lastrowid, title, lesson_order),
    ).lastrowid
    conn.commit()
    return lid


# --- Reminders -------------------------------------------------------------------


def test_reminder_is_sent_only_once_per_pause(conn):
    from app.notifications import send_reminders

    _inactive_user(conn, 1)
    sender = FakeSender()
    assert send_reminders(conn, _settings(), sender=sender) == 1
    assert send_reminders(conn, _settings(), sender=sender) == 0
    assert len(sender.calls) == 1


def test_reminder_is_sent_again_after_user_returns_and_goes_quiet(conn):
    from app.notifications import send_reminders

    _inactive_user(conn, 1, days=20)
    send_reminders(conn, _settings(), sender=FakeSender())
    # User came back after the reminder, then went quiet again.
    conn.execute("UPDATE users SET last_reminded_at = ?",
                 ((datetime.now(timezone.utc) - timedelta(days=15)).isoformat(),))
    _inactive_user(conn, 1, days=10)
    sender = FakeSender()
    assert send_reminders(conn, _settings(), sender=sender) == 1


def test_users_with_notifications_off_get_nothing(conn):
    from app.notifications import broadcast, send_reminders

    _inactive_user(conn, 1)
    set_notifications(conn, 1, False)
    sender = FakeSender()
    assert send_reminders(conn, _settings(), sender=sender) == 0
    assert broadcast(conn, _settings(), "hi", sender=sender) == 0
    assert broadcast(conn, _settings(), "hi", only_inactive_days=3, sender=sender) == 0
    assert sender.calls == []


def test_reminder_names_next_unfinished_lesson_with_button(conn):
    from app.notifications import send_reminders

    first = _lesson(conn, "Бюджет", topic_order=0)
    second = _lesson(conn, "Кредиты", topic_order=1)
    _inactive_user(conn, 1)
    conn.execute(
        "INSERT INTO progress (telegram_id, lesson_id, completed_at, last_activity_at) "
        "VALUES (1, ?, '2020-01-01', '2020-01-01')",
        (first,),
    )
    conn.commit()
    sender = FakeSender()
    send_reminders(conn, _settings(), sender=sender)
    payload = sender.calls[0][1]
    assert "Кредиты" in payload["text"]
    button = payload["reply_markup"]["inline_keyboard"][0][0]
    assert button["web_app"]["url"] == f"https://example.test/lessons/{second}"


def test_next_lesson_prefers_started_topic(conn):
    from app.notifications import next_lesson_for

    _lesson(conn, "A", topic_order=0)
    started_topic_lesson = _lesson(conn, "B1", topic_order=1, lesson_order=0)
    topic_b = conn.execute("SELECT topic_id FROM lessons WHERE id = ?", (started_topic_lesson,)).fetchone()[0]
    b2 = conn.execute(
        "INSERT INTO lessons (topic_id, title, \"order\", is_published) VALUES (?, 'B2', 1, 1)", (topic_b,)
    ).lastrowid
    conn.execute(
        "INSERT INTO progress (telegram_id, lesson_id, completed_at) VALUES (1, ?, '2020-01-01')",
        (started_topic_lesson,),
    )
    conn.commit()
    assert next_lesson_for(conn, 1)["id"] == b2


# --- Bot ---------------------------------------------------------------------------


@pytest.mark.parametrize("text", ["/start", "/start promo", "/start@finedu_bot"])
def test_start_replies_with_open_app_button(conn, text):
    from app.scripts.bot import dispatch

    sender = FakeSender()
    update = {"message": {"text": text, "chat": {"id": 5, "type": "private"}}}
    dispatch(conn, _settings(), update, sender=sender)
    button = sender.calls[0][1]["reply_markup"]["inline_keyboard"][0][0]
    assert button["web_app"]["url"] == "https://example.test"


def test_bot_ignores_group_chats(conn):
    from app.scripts.bot import dispatch

    sender = FakeSender()
    update = {"message": {"text": "/delete_my_data", "chat": {"id": -100, "type": "group"}}}
    dispatch(conn, _settings(), update, sender=sender)
    assert sender.calls == []


# --- Notifications API ---------------------------------------------------------


@pytest.fixture
def client(conn):
    def _override_db():
        yield conn

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_settings] = _settings
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_settings, None)


def test_notifications_api_requires_telegram(client):
    assert client.get("/api/users/me/notifications").status_code == 403
    assert client.put("/api/users/me/notifications", json={"enabled": False}).status_code == 403


def test_user_can_turn_notifications_off_and_on(client, conn, make_init_data):
    headers = {"X-Telegram-Init-Data": make_init_data(user_id=42, bot_token=TEST_BOT_TOKEN)}
    assert client.get("/api/users/me/notifications", headers=headers).json() == {"enabled": True}
    resp = client.put("/api/users/me/notifications", json={"enabled": False}, headers=headers)
    assert resp.json() == {"enabled": False}
    row = conn.execute("SELECT notifications_enabled FROM users WHERE telegram_id = 42").fetchone()
    assert row[0] == 0
    resp = client.put("/api/users/me/notifications", json={"enabled": True}, headers=headers)
    assert resp.json() == {"enabled": True}


def test_migration_adds_column_to_old_database(tmp_path):
    c = get_connection(str(tmp_path / "old.db"))
    c.execute(
        "CREATE TABLE users (telegram_id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, "
        "notifications_enabled INTEGER NOT NULL DEFAULT 1)"
    )
    c.commit()
    init_db(c)
    columns = {r["name"] for r in c.execute("PRAGMA table_info(users)")}
    assert "last_reminded_at" in columns

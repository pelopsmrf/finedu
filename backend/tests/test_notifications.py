from datetime import datetime, timedelta, timezone

import pytest

from app.config import Settings
from app.db import ensure_user, get_connection, init_db


class FakeResponse:
    def __init__(self, status_code=200):
        self.status_code = status_code


class FakeSender:
    def __init__(self):
        self.calls = []

    def __call__(self, url, json=None, timeout=10):
        self.calls.append((url, json))
        return FakeResponse(200)


def _settings(reminder_days=3):
    return Settings(bot_token="tkn", admin_id=1, db_path=":memory:", reminder_days=reminder_days)


@pytest.fixture
def conn(tmp_path):
    c = get_connection(str(tmp_path / "notif.db"))
    init_db(c)
    return c


def _set_last_activity(conn, telegram_id, dt):
    ensure_user(conn, telegram_id, dt.isoformat())
    conn.execute(
        "INSERT INTO progress (telegram_id, last_activity_at) VALUES (?, ?)",
        (telegram_id, dt.isoformat()),
    )
    conn.commit()


def test_find_inactive_users_returns_only_stale(conn):
    from app.notifications import find_inactive_users

    now = datetime.now(timezone.utc)
    _set_last_activity(conn, 1, now - timedelta(days=10))
    _set_last_activity(conn, 2, now - timedelta(hours=1))
    result = find_inactive_users(conn, days=3)
    assert result == [1]


def test_send_reminders_calls_sender_per_inactive_user(conn):
    from app.notifications import send_reminders

    now = datetime.now(timezone.utc)
    _set_last_activity(conn, 1, now - timedelta(days=10))
    _set_last_activity(conn, 2, now - timedelta(hours=1))
    sender = FakeSender()
    count = send_reminders(conn, _settings(), sender=sender)
    assert count == 1
    assert len(sender.calls) == 1
    assert sender.calls[0][1]["chat_id"] == 1


def test_broadcast_with_no_matching_inactive_users_returns_zero(conn):
    from app.notifications import broadcast

    now = datetime.now(timezone.utc)
    _set_last_activity(conn, 1, now - timedelta(hours=1))
    sender = FakeSender()
    count = broadcast(conn, _settings(), "hi", only_inactive_days=30, sender=sender)
    assert count == 0
    assert sender.calls == []


def test_broadcast_to_all_users(conn):
    from app.notifications import broadcast

    now = datetime.now(timezone.utc)
    _set_last_activity(conn, 1, now)
    _set_last_activity(conn, 2, now)
    sender = FakeSender()
    count = broadcast(conn, _settings(), "hi", only_inactive_days=None, sender=sender)
    assert count == 2


def test_delete_my_data_handler_removes_user_and_replies(conn):
    from app.scripts.bot import handle_delete_my_data

    ensure_user(conn, 1, datetime.now(timezone.utc).isoformat())
    conn.execute("INSERT INTO progress (telegram_id, lesson_id) VALUES (1, 1)")
    conn.commit()
    sender = FakeSender()

    handle_delete_my_data(conn, chat_id=1, bot_token="tkn", sender=sender)

    assert conn.execute("SELECT * FROM users WHERE telegram_id = 1").fetchone() is None
    assert conn.execute("SELECT * FROM progress WHERE telegram_id = 1").fetchone() is None
    assert len(sender.calls) == 1
    assert sender.calls[0][1]["chat_id"] == 1

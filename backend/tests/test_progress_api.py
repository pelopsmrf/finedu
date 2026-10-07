import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.db import get_connection, get_db, init_db
from app.main import app

ADMIN_ID = 777
OTHER_USER_ID = 555
TEST_BOT_TOKEN = "test-bot-token"  # noqa: S105 - test fixture only


def _test_settings() -> Settings:
    return Settings(bot_token=TEST_BOT_TOKEN, admin_id=ADMIN_ID, db_path=":memory:")


@pytest.fixture
def seed_db(tmp_path):
    conn = get_connection(str(tmp_path / "progress.db"))
    init_db(conn)

    def _override_db():
        try:
            yield conn
        finally:
            pass

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_settings] = _test_settings
    yield conn
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_settings, None)
    conn.close()


@pytest.fixture
def client(seed_db):
    return TestClient(app)


def test_post_progress_requires_verified_user(client, seed_db):
    resp = client.post("/api/progress", json={"lesson_id": 1})
    assert resp.status_code in (401, 403)
    count = seed_db.execute("SELECT COUNT(*) FROM progress").fetchone()[0]
    assert count == 0


def test_post_progress_uses_verified_telegram_id_ignoring_body(
    client, seed_db, make_init_data
):
    init_data = make_init_data(user_id=OTHER_USER_ID, bot_token=TEST_BOT_TOKEN)
    resp = client.post(
        "/api/progress",
        json={"lesson_id": 1, "quiz_id": 2, "quiz_score": 3, "telegram_id": 999999},
        headers={"X-Telegram-Init-Data": init_data},
    )
    assert resp.status_code == 200
    row = seed_db.execute("SELECT telegram_id FROM progress").fetchone()
    assert row["telegram_id"] == OTHER_USER_ID


def test_progress_me_returns_only_callers_rows(client, seed_db, make_init_data):
    user_a = make_init_data(user_id=OTHER_USER_ID, bot_token=TEST_BOT_TOKEN)
    user_b = make_init_data(user_id=ADMIN_ID, bot_token=TEST_BOT_TOKEN)
    client.post(
        "/api/progress", json={"lesson_id": 1}, headers={"X-Telegram-Init-Data": user_a}
    )
    client.post(
        "/api/progress", json={"lesson_id": 2}, headers={"X-Telegram-Init-Data": user_b}
    )
    resp = client.get("/api/progress/me", headers={"X-Telegram-Init-Data": user_a})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["progress"]) == 1
    assert body["progress"][0]["lesson_id"] == 1


def test_delete_my_data_removes_only_own_rows(client, seed_db, make_init_data):
    user_a = make_init_data(user_id=OTHER_USER_ID, bot_token=TEST_BOT_TOKEN)
    user_b = make_init_data(user_id=ADMIN_ID, bot_token=TEST_BOT_TOKEN)
    client.post(
        "/api/progress", json={"lesson_id": 1}, headers={"X-Telegram-Init-Data": user_a}
    )
    client.post(
        "/api/progress", json={"lesson_id": 2}, headers={"X-Telegram-Init-Data": user_b}
    )
    resp = client.delete("/api/users/me", headers={"X-Telegram-Init-Data": user_a})
    assert resp.status_code == 200
    assert resp.json() == {"deleted": True}

    remaining_users = {
        r["telegram_id"] for r in seed_db.execute("SELECT telegram_id FROM users")
    }
    assert OTHER_USER_ID not in remaining_users
    assert ADMIN_ID in remaining_users

    remaining_progress = {
        r["telegram_id"] for r in seed_db.execute("SELECT telegram_id FROM progress")
    }
    assert OTHER_USER_ID not in remaining_progress
    assert ADMIN_ID in remaining_progress

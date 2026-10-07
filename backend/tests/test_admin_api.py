import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.db import get_connection, get_db, init_db
from app.main import app

ADMIN_ID = 777
NON_ADMIN_ID = 555
TEST_BOT_TOKEN = "test-bot-token"  # noqa: S105 - test fixture only


def _test_settings() -> Settings:
    return Settings(bot_token=TEST_BOT_TOKEN, admin_id=ADMIN_ID, db_path=":memory:")


@pytest.fixture
def seed_db(tmp_path):
    conn = get_connection(str(tmp_path / "admin.db"))
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


@pytest.fixture
def admin_headers(make_init_data):
    data = make_init_data(user_id=ADMIN_ID, bot_token=TEST_BOT_TOKEN)
    return {"X-Telegram-Init-Data": data}


@pytest.fixture
def non_admin_headers(make_init_data):
    data = make_init_data(user_id=NON_ADMIN_ID, bot_token=TEST_BOT_TOKEN)
    return {"X-Telegram-Init-Data": data}


def test_create_topic_requires_admin(client, non_admin_headers):
    resp = client.post(
        "/api/admin/topics",
        json={"title": "Бюджет", "is_published": True},
        headers=non_admin_headers,
    )
    assert resp.status_code == 403


def test_create_topic_and_see_it_in_public_list(client, admin_headers):
    resp = client.post(
        "/api/admin/topics",
        json={"title": "Бюджет", "order": 1, "is_published": True},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    topic_id = resp.json()["id"]

    public_resp = client.get("/api/topics")
    assert topic_id in [t["id"] for t in public_resp.json()]


def test_update_topic_requires_admin_and_persists(client, admin_headers, non_admin_headers):
    created = client.post(
        "/api/admin/topics",
        json={"title": "Draft", "is_published": False},
        headers=admin_headers,
    ).json()
    topic_id = created["id"]

    denied = client.put(
        f"/api/admin/topics/{topic_id}",
        json={"title": "Published", "is_published": True},
        headers=non_admin_headers,
    )
    assert denied.status_code == 403

    allowed = client.put(
        f"/api/admin/topics/{topic_id}",
        json={"title": "Published", "is_published": True},
        headers=admin_headers,
    )
    assert allowed.status_code == 200
    assert allowed.json()["title"] == "Published"

    public_resp = client.get("/api/topics")
    titles = [t["title"] for t in public_resp.json()]
    assert "Published" in titles


def test_delete_topic_requires_admin_and_persists(client, admin_headers, non_admin_headers):
    created = client.post(
        "/api/admin/topics",
        json={"title": "Temp", "is_published": True},
        headers=admin_headers,
    ).json()
    topic_id = created["id"]

    denied = client.delete(f"/api/admin/topics/{topic_id}", headers=non_admin_headers)
    assert denied.status_code == 403

    allowed = client.delete(f"/api/admin/topics/{topic_id}", headers=admin_headers)
    assert allowed.status_code == 200

    public_resp = client.get("/api/topics")
    assert topic_id not in [t["id"] for t in public_resp.json()]


def test_lesson_crud_requires_admin_and_persists(client, admin_headers, non_admin_headers):
    topic = client.post(
        "/api/admin/topics",
        json={"title": "Бюджет", "is_published": True},
        headers=admin_headers,
    ).json()

    denied = client.post(
        "/api/admin/lessons",
        json={"topic_id": topic["id"], "title": "Урок 1", "is_published": True},
        headers=non_admin_headers,
    )
    assert denied.status_code == 403

    created = client.post(
        "/api/admin/lessons",
        json={"topic_id": topic["id"], "title": "Урок 1", "is_published": True},
        headers=admin_headers,
    ).json()

    public_resp = client.get(f"/api/topics/{topic['id']}/lessons")
    assert created["id"] in [l["id"] for l in public_resp.json()]

    updated = client.put(
        f"/api/admin/lessons/{created['id']}",
        json={"topic_id": topic["id"], "title": "Урок 1 (ред.)", "is_published": True},
        headers=admin_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Урок 1 (ред.)"

    deleted = client.delete(f"/api/admin/lessons/{created['id']}", headers=admin_headers)
    assert deleted.status_code == 200
    public_resp = client.get(f"/api/topics/{topic['id']}/lessons")
    assert created["id"] not in [l["id"] for l in public_resp.json()]


def test_quiz_crud_requires_admin_and_persists(client, admin_headers, non_admin_headers):
    denied = client.post(
        "/api/admin/quizzes",
        json={"title": "Квиз", "is_published": True},
        headers=non_admin_headers,
    )
    assert denied.status_code == 403

    created = client.post(
        "/api/admin/quizzes",
        json={"title": "Квиз", "is_published": True},
        headers=admin_headers,
    ).json()

    public_resp = client.get("/api/quizzes")
    assert created["id"] in [q["id"] for q in public_resp.json()]

    updated = client.put(
        f"/api/admin/quizzes/{created['id']}",
        json={"title": "Квиз (ред.)", "is_published": True},
        headers=admin_headers,
    )
    assert updated.status_code == 200

    deleted = client.delete(f"/api/admin/quizzes/{created['id']}", headers=admin_headers)
    assert deleted.status_code == 200
    public_resp = client.get("/api/quizzes")
    assert created["id"] not in [q["id"] for q in public_resp.json()]

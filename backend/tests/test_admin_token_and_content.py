"""Admin login by secret token, draft lists, content validation, cascade delete."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.db import get_connection, get_db, init_db
from app.main import app

ADMIN_ID = 777
TEST_BOT_TOKEN = "test-bot-token"  # noqa: S105 - test fixture only
ADMIN_TOKEN = "a" * 40  # noqa: S105 - test fixture only


@pytest.fixture
def settings_holder():
    return {"settings": Settings(
        bot_token=TEST_BOT_TOKEN, admin_id=ADMIN_ID, db_path=":memory:", admin_token=ADMIN_TOKEN
    )}


@pytest.fixture
def seed_db(tmp_path, settings_holder):
    conn = get_connection(str(tmp_path / "admin2.db"))
    init_db(conn)

    def _override_db():
        yield conn

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_settings] = lambda: settings_holder["settings"]
    yield conn
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_settings, None)
    conn.close()


@pytest.fixture
def client(seed_db):
    return TestClient(app)


@pytest.fixture
def token_headers():
    return {"X-Admin-Token": ADMIN_TOKEN}


# --- Token login ---------------------------------------------------------------


def test_correct_admin_token_grants_access(client, token_headers):
    assert client.get("/api/admin/_probe", headers=token_headers).status_code == 200


def test_wrong_admin_token_is_rejected(client):
    resp = client.get("/api/admin/_probe", headers={"X-Admin-Token": "b" * 40})
    assert resp.status_code == 403


def test_empty_admin_token_is_rejected(client):
    assert client.get("/api/admin/_probe", headers={"X-Admin-Token": ""}).status_code == 403


def test_token_ignored_when_not_configured(client, settings_holder):
    settings_holder["settings"] = Settings(
        bot_token=TEST_BOT_TOKEN, admin_id=ADMIN_ID, db_path=":memory:", admin_token=None
    )
    resp = client.get("/api/admin/_probe", headers={"X-Admin-Token": ""})
    assert resp.status_code == 403


def test_too_short_configured_token_is_never_accepted(client, settings_holder):
    settings_holder["settings"] = Settings(
        bot_token=TEST_BOT_TOKEN, admin_id=ADMIN_ID, db_path=":memory:", admin_token="123"
    )
    resp = client.get("/api/admin/_probe", headers={"X-Admin-Token": "123"})
    assert resp.status_code == 403


def test_telegram_admin_still_works_alongside_token(client, make_init_data):
    headers = {"X-Telegram-Init-Data": make_init_data(user_id=ADMIN_ID, bot_token=TEST_BOT_TOKEN)}
    assert client.get("/api/admin/_probe", headers=headers).status_code == 200


def test_admin_lists_require_admin(client):
    for path in ["/api/admin/topics", "/api/admin/quizzes", "/api/admin/topics/1/lessons"]:
        assert client.get(path).status_code == 403


# --- Drafts are visible in the admin panel -------------------------------------


def test_admin_sees_draft_topics_lessons_and_quizzes(client, token_headers):
    topic = client.post(
        "/api/admin/topics", json={"title": "Черновик"}, headers=token_headers
    ).json()
    lesson = client.post(
        "/api/admin/lessons", json={"topic_id": topic["id"], "title": "Урок"}, headers=token_headers
    ).json()
    client.post(
        "/api/admin/quizzes", json={"lesson_id": lesson["id"], "title": "Квиз"}, headers=token_headers
    )

    assert client.get("/api/topics").json() == []
    topics = client.get("/api/admin/topics", headers=token_headers).json()
    assert [t["title"] for t in topics] == ["Черновик"]
    lessons = client.get(f"/api/admin/topics/{topic['id']}/lessons", headers=token_headers).json()
    assert [lesson_["title"] for lesson_ in lessons] == ["Урок"]
    quizzes = client.get(
        f"/api/admin/quizzes?lesson_id={lesson['id']}", headers=token_headers
    ).json()
    assert [q["title"] for q in quizzes] == ["Квиз"]
    assert client.get(f"/api/admin/lessons/{lesson['id']}", headers=token_headers).status_code == 200


# --- Validation ----------------------------------------------------------------


def test_lesson_steps_are_saved_without_empty_fields(client, token_headers):
    topic = client.post("/api/admin/topics", json={"title": "T"}, headers=token_headers).json()
    lesson = client.post(
        "/api/admin/lessons",
        json={"topic_id": topic["id"], "title": "Урок", "content": [{"text": "Привет", "emoji": "👋"}]},
        headers=token_headers,
    ).json()
    assert lesson["content"] == [{"type": "text", "text": "Привет", "emoji": "👋"}]


def test_lesson_for_missing_topic_is_rejected(client, token_headers):
    resp = client.post("/api/admin/lessons", json={"topic_id": 999, "title": "X"}, headers=token_headers)
    assert resp.status_code == 404


@pytest.mark.parametrize(
    "question",
    [
        {"question": "Q", "options": ["one"], "correct_index": 0},
        {"question": "Q", "options": ["a", "b"], "correct_index": 2},
        {"question": "", "options": ["a", "b"], "correct_index": 0},
    ],
)
def test_invalid_quiz_question_is_rejected(client, token_headers, question):
    resp = client.post(
        "/api/admin/quizzes", json={"title": "Квиз", "questions": [question]}, headers=token_headers
    )
    assert resp.status_code == 422


def test_empty_title_is_rejected(client, token_headers):
    assert client.post("/api/admin/topics", json={"title": ""}, headers=token_headers).status_code == 422


# --- Cascade delete -------------------------------------------------------------


def test_deleting_topic_removes_its_lessons_and_their_quizzes(client, token_headers, seed_db):
    topic = client.post("/api/admin/topics", json={"title": "T"}, headers=token_headers).json()
    lesson = client.post(
        "/api/admin/lessons", json={"topic_id": topic["id"], "title": "L"}, headers=token_headers
    ).json()
    client.post("/api/admin/quizzes", json={"lesson_id": lesson["id"], "title": "Q"}, headers=token_headers)
    client.post("/api/admin/quizzes", json={"title": "Standalone"}, headers=token_headers)

    client.delete(f"/api/admin/topics/{topic['id']}", headers=token_headers)

    assert seed_db.execute("SELECT COUNT(*) FROM lessons").fetchone()[0] == 0
    titles = [r[0] for r in seed_db.execute("SELECT title FROM quizzes")]
    assert titles == ["Standalone"]


def test_deleting_lesson_removes_its_quizzes(client, token_headers, seed_db):
    topic = client.post("/api/admin/topics", json={"title": "T"}, headers=token_headers).json()
    lesson = client.post(
        "/api/admin/lessons", json={"topic_id": topic["id"], "title": "L"}, headers=token_headers
    ).json()
    client.post("/api/admin/quizzes", json={"lesson_id": lesson["id"], "title": "Q"}, headers=token_headers)

    client.delete(f"/api/admin/lessons/{lesson['id']}", headers=token_headers)

    assert seed_db.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0] == 0

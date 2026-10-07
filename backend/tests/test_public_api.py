import json

import pytest
from fastapi.testclient import TestClient

from app.db import get_db, get_connection, init_db
from app.main import app


@pytest.fixture
def seed_db(tmp_path):
    conn = get_connection(str(tmp_path / "public.db"))
    init_db(conn)

    def _override():
        try:
            yield conn
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    yield conn
    app.dependency_overrides.pop(get_db, None)
    conn.close()


@pytest.fixture
def client(seed_db):
    return TestClient(app)


def _insert_topic(conn, title, order=0, is_published=1):
    cur = conn.execute(
        'INSERT INTO topics (title, description, icon, "order", is_published) '
        "VALUES (?, '', '', ?, ?)",
        (title, order, is_published),
    )
    conn.commit()
    return cur.lastrowid


def _insert_lesson(conn, topic_id, title, order=0, is_published=1, content=None):
    cur = conn.execute(
        'INSERT INTO lessons (topic_id, title, "order", content, is_published) '
        "VALUES (?, ?, ?, ?, ?)",
        (topic_id, title, order, json.dumps(content or []), is_published),
    )
    conn.commit()
    return cur.lastrowid


def _insert_quiz(conn, title, lesson_id=None, is_published=1, questions=None):
    cur = conn.execute(
        "INSERT INTO quizzes (lesson_id, title, questions, is_published) "
        "VALUES (?, ?, ?, ?)",
        (lesson_id, title, json.dumps(questions or []), is_published),
    )
    conn.commit()
    return cur.lastrowid


def test_list_topics_excludes_unpublished(client, seed_db):
    _insert_topic(seed_db, "Бюджет", order=1)
    _insert_topic(seed_db, "Draft topic", order=2, is_published=0)
    resp = client.get("/api/topics")
    assert resp.status_code == 200
    titles = [t["title"] for t in resp.json()]
    assert titles == ["Бюджет"]


def test_list_topic_lessons_excludes_unpublished(client, seed_db):
    topic_id = _insert_topic(seed_db, "Бюджет")
    _insert_lesson(seed_db, topic_id, "Урок 1", order=1)
    _insert_lesson(seed_db, topic_id, "Draft урок", order=2, is_published=0)
    resp = client.get(f"/api/topics/{topic_id}/lessons")
    assert resp.status_code == 200
    titles = [l["title"] for l in resp.json()]
    assert titles == ["Урок 1"]


def test_get_lesson_404_for_missing(client, seed_db):
    resp = client.get("/api/lessons/9999")
    assert resp.status_code == 404


def test_get_lesson_returns_content(client, seed_db):
    topic_id = _insert_topic(seed_db, "Бюджет")
    lesson_id = _insert_lesson(
        seed_db, topic_id, "Урок 1", content=[{"type": "text", "text": "hi"}]
    )
    resp = client.get(f"/api/lessons/{lesson_id}")
    assert resp.status_code == 200
    assert resp.json()["content"] == [{"type": "text", "text": "hi"}]


def test_list_quizzes_only_standalone_and_published(client, seed_db):
    topic_id = _insert_topic(seed_db, "Бюджет")
    lesson_id = _insert_lesson(seed_db, topic_id, "Урок 1")
    _insert_quiz(seed_db, "Standalone", lesson_id=None)
    _insert_quiz(seed_db, "Lesson quiz", lesson_id=lesson_id)
    _insert_quiz(seed_db, "Draft standalone", lesson_id=None, is_published=0)
    resp = client.get("/api/quizzes")
    assert resp.status_code == 200
    titles = [q["title"] for q in resp.json()]
    assert titles == ["Standalone"]


def test_get_quiz_404_for_missing(client, seed_db):
    resp = client.get("/api/quizzes/9999")
    assert resp.status_code == 404


def test_quiz_with_malformed_questions_json_is_skipped(client, seed_db):
    seed_db.execute(
        "INSERT INTO quizzes (title, questions, lesson_id, is_published) "
        "VALUES ('broken', 'not json', NULL, 1)"
    )
    seed_db.commit()
    resp = client.get("/api/quizzes")
    assert resp.status_code == 200
    assert "broken" not in [q["title"] for q in resp.json()]

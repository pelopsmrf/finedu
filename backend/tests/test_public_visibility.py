"""Content of unpublished topics stays hidden; lesson quiz endpoint; topic by id."""

import json

import pytest
from fastapi.testclient import TestClient

from app.db import get_connection, get_db, init_db
from app.main import app

QUESTION = {"question": "2+2?", "options": ["3", "4"], "correct_index": 1}


@pytest.fixture
def seed_db(tmp_path):
    conn = get_connection(str(tmp_path / "vis.db"))
    init_db(conn)

    def _override():
        yield conn

    app.dependency_overrides[get_db] = _override
    yield conn
    app.dependency_overrides.pop(get_db, None)
    conn.close()


@pytest.fixture
def client(seed_db):
    return TestClient(app)


def _topic(conn, published=1):
    cur = conn.execute(
        'INSERT INTO topics (title, "order", is_published) VALUES (?, 0, ?)', ("T", published)
    )
    conn.commit()
    return cur.lastrowid


def _lesson(conn, topic_id, published=1):
    cur = conn.execute(
        "INSERT INTO lessons (topic_id, title, content, is_published) VALUES (?, 'L', '[]', ?)",
        (topic_id, published),
    )
    conn.commit()
    return cur.lastrowid


def _quiz(conn, lesson_id, published=1, questions=(QUESTION,)):
    cur = conn.execute(
        "INSERT INTO quizzes (lesson_id, title, questions, is_published) VALUES (?, 'Q', ?, ?)",
        (lesson_id, json.dumps(list(questions)), published),
    )
    conn.commit()
    return cur.lastrowid


def test_lessons_of_unpublished_topic_are_hidden(client, seed_db):
    topic_id = _topic(seed_db, published=0)
    lesson_id = _lesson(seed_db, topic_id)
    quiz_id = _quiz(seed_db, lesson_id)
    assert client.get(f"/api/topics/{topic_id}").status_code == 404
    assert client.get(f"/api/topics/{topic_id}/lessons").json() == []
    assert client.get(f"/api/lessons/{lesson_id}").status_code == 404
    assert client.get(f"/api/lessons/{lesson_id}/quiz").status_code == 404
    assert client.get(f"/api/quizzes/{quiz_id}").status_code == 404


def test_get_published_topic(client, seed_db):
    topic_id = _topic(seed_db)
    assert client.get(f"/api/topics/{topic_id}").json()["title"] == "T"


def test_lesson_quiz_returns_published_quiz(client, seed_db):
    lesson_id = _lesson(seed_db, _topic(seed_db))
    _quiz(seed_db, lesson_id, published=0)
    quiz_id = _quiz(seed_db, lesson_id)
    resp = client.get(f"/api/lessons/{lesson_id}/quiz")
    assert resp.status_code == 200
    assert resp.json()["id"] == quiz_id


def test_lesson_quiz_404_when_no_questions(client, seed_db):
    lesson_id = _lesson(seed_db, _topic(seed_db))
    _quiz(seed_db, lesson_id, questions=())
    assert client.get(f"/api/lessons/{lesson_id}/quiz").status_code == 404

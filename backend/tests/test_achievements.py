import json

import pytest
from fastapi.testclient import TestClient

from app.achievements import summarize
from app.config import Settings, get_settings
from app.db import get_connection, get_db, init_db
from app.main import app

USER_ID = 555
TEST_BOT_TOKEN = "test-bot-token"  # noqa: S105 - test fixture only


def _test_settings() -> Settings:
    return Settings(bot_token=TEST_BOT_TOKEN, admin_id=777, db_path=":memory:")


@pytest.fixture
def seed_db(tmp_path):
    conn = get_connection(str(tmp_path / "badges.db"))
    init_db(conn)
    # Topic 1: lessons 1, 2 (+ hidden draft 3). Topic 2: lesson 4. Hidden topic 3: lesson 5.
    conn.executescript(
        """
        INSERT INTO topics (id, title, icon, "order", is_published) VALUES
            (1, 'Бюджет', '💰', 1, 1), (2, 'Кредиты', '💳', 2, 1), (3, 'Черновик', '📝', 3, 0);
        INSERT INTO lessons (id, topic_id, title, "order", is_published) VALUES
            (1, 1, 'У1', 1, 1), (2, 1, 'У2', 2, 1), (3, 1, 'Черновик', 3, 0),
            (4, 2, 'У4', 1, 1), (5, 3, 'У5', 1, 1);
        """
    )
    for quiz_id in range(1, 7):
        questions = [{"question": "?", "options": ["a", "b"], "correct_index": 0}] * 2
        conn.execute(
            "INSERT INTO quizzes (id, lesson_id, title, questions, is_published) "
            "VALUES (?, NULL, ?, ?, 1)",
            (quiz_id, f"Квиз {quiz_id}", json.dumps(questions)),
        )
    conn.commit()

    def _override_db():
        yield conn

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_settings] = _test_settings
    yield conn
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_settings, None)
    conn.close()


@pytest.fixture
def post(seed_db, make_init_data):
    client = TestClient(app)
    headers = {"X-Telegram-Init-Data": make_init_data(user_id=USER_ID, bot_token=TEST_BOT_TOKEN)}

    def _post(**payload):
        resp = client.post("/api/progress", json=payload, headers=headers)
        assert resp.status_code == 200
        return [b["id"] for b in resp.json()["new_badges"]]

    _post.get = lambda: client.get("/api/progress/me", headers=headers).json()
    return _post


def _earned(summary):
    return {b["id"] for b in summary["badges"] if b["earned"]}


def test_new_user_has_no_badges_and_sees_visible_topics_only(post):
    summary = post.get()
    assert _earned(summary) == set()
    assert [(t["topic_id"], t["completed"], t["total"]) for t in summary["topics"]] == [
        (1, 0, 2),
        (2, 0, 1),
    ]
    assert summary["total_lessons"] == 3
    assert len(summary["badges"]) == 6


def test_lessons_give_first_step_topic_and_all_done(post):
    assert post(lesson_id=1) == ["first_lesson"]
    assert post(lesson_id=1) == []  # repeating a lesson gives nothing new
    assert post(lesson_id=2) == ["topic_done"]
    assert post(lesson_id=4) == ["all_done"]
    summary = post.get()
    assert summary["completed_lessons"] == 3
    assert [t["completed"] for t in summary["topics"]] == [2, 1]


def test_hidden_lessons_do_not_count(post):
    post(lesson_id=3)
    post(lesson_id=5)
    summary = post.get()
    assert summary["completed_lessons"] == 0
    assert "first_lesson" not in _earned(summary)


def test_perfect_quiz_needs_all_answers_right(post):
    assert post(quiz_id=1, quiz_score=1) == []
    assert post(quiz_id=1, quiz_score=2) == ["perfect_quiz"]


def test_five_different_quizzes(post):
    for quiz_id in (1, 1, 2, 3, 4):
        assert post(quiz_id=quiz_id, quiz_score=0) == []
    assert post(quiz_id=5, quiz_score=0) == ["five_quizzes"]


def _add_activity(conn, *moments):
    for moment in moments:
        conn.execute(
            "INSERT INTO progress (telegram_id, quiz_id, quiz_score, last_activity_at) "
            "VALUES (?, 1, 0, ?)",
            (USER_ID, moment),
        )
    conn.commit()


def test_streak_counts_three_moscow_days_in_a_row(seed_db):
    # 21:30 UTC on the 9th is already the 10th in Moscow.
    _add_activity(seed_db, "2026-10-09T10:00:00+00:00", "2026-10-09T21:30:00+00:00",
                  "2026-10-11T09:00:00+00:00")
    assert "streak_3" in _earned(summarize(seed_db, USER_ID))


def test_streak_breaks_on_a_missed_day(seed_db):
    _add_activity(seed_db, "2026-10-09T10:00:00+00:00", "2026-10-10T10:00:00+00:00",
                  "2026-10-12T10:00:00+00:00", "2026-10-13T10:00:00+00:00")
    assert "streak_3" not in _earned(summarize(seed_db, USER_ID))

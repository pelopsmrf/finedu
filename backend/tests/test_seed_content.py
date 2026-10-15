import json

from app.db import get_connection, init_db
from app.scripts.seed_content import DEFAULT_FILE, seed


def _conn(tmp_path):
    conn = get_connection(str(tmp_path / "seed.db"))
    init_db(conn)
    return conn


def test_starter_content_loads_and_is_valid(tmp_path):
    conn = _conn(tmp_path)
    added = seed(conn, json.loads(DEFAULT_FILE.read_text(encoding="utf-8")))
    assert added == {"topics": 3, "lessons": 9, "quizzes": 11}
    # Every lesson got a quiz.
    orphan = conn.execute(
        "SELECT COUNT(*) FROM lessons WHERE id NOT IN (SELECT lesson_id FROM quizzes WHERE lesson_id IS NOT NULL)"
    ).fetchone()[0]
    assert orphan == 0


def test_seed_twice_adds_nothing_and_keeps_edits(tmp_path):
    conn = _conn(tmp_path)
    data = json.loads(DEFAULT_FILE.read_text(encoding="utf-8"))
    seed(conn, data)
    conn.execute("UPDATE lessons SET title = 'Изменено в админке' WHERE id = 1")
    conn.commit()
    assert seed(conn, data) == {"topics": 0, "lessons": 0, "quizzes": 0}
    assert conn.execute("SELECT title FROM lessons WHERE id = 1").fetchone()[0] == "Изменено в админке"

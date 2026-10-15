"""Load starter topics, lessons and quizzes into the database.

    python -m app.scripts.seed_content                 # backend/content/starter.json
    python -m app.scripts.seed_content path/to/file.json

Safe to run again: a topic (or standalone quiz) whose title already exists
is skipped, so nothing you edited in the admin panel is overwritten.
"""

import json
import sqlite3
import sys
from pathlib import Path

from app.config import get_settings
from app.db import get_connection, init_db
from app.schemas import LessonStep, QuizQuestion

DEFAULT_FILE = Path(__file__).resolve().parents[2] / "content" / "starter.json"


def _dump(items: list[dict], model) -> str:
    # Validate through the same schemas as the admin API.
    return json.dumps(
        [model(**item).model_dump(exclude_none=True) for item in items], ensure_ascii=False
    )


def _insert_quiz(conn: sqlite3.Connection, quiz: dict, lesson_id: int | None) -> None:
    conn.execute(
        "INSERT INTO quizzes (lesson_id, title, questions, is_published) VALUES (?, ?, ?, ?)",
        (lesson_id, quiz["title"], _dump(quiz["questions"], QuizQuestion), int(quiz.get("published", True))),
    )


def seed(conn: sqlite3.Connection, data: dict) -> dict:
    """Insert content that is not in the database yet. Returns what was added."""
    added = {"topics": 0, "lessons": 0, "quizzes": 0}
    for topic in data.get("topics", []):
        if conn.execute("SELECT 1 FROM topics WHERE title = ?", (topic["title"],)).fetchone():
            continue
        topic_id = conn.execute(
            'INSERT INTO topics (title, description, icon, "order", is_published) VALUES (?, ?, ?, ?, ?)',
            (topic["title"], topic.get("description"), topic.get("icon"), topic.get("order", 0),
             int(topic.get("published", True))),
        ).lastrowid
        added["topics"] += 1
        for order, lesson in enumerate(topic.get("lessons", []), start=1):
            lesson_id = conn.execute(
                'INSERT INTO lessons (topic_id, title, "order", content, is_published) VALUES (?, ?, ?, ?, ?)',
                (topic_id, lesson["title"], order, _dump(lesson["steps"], LessonStep),
                 int(lesson.get("published", True))),
            ).lastrowid
            added["lessons"] += 1
            if lesson.get("quiz"):
                _insert_quiz(conn, lesson["quiz"], lesson_id)
                added["quizzes"] += 1
    for quiz in data.get("quizzes", []):
        exists = conn.execute(
            "SELECT 1 FROM quizzes WHERE lesson_id IS NULL AND title = ?", (quiz["title"],)
        ).fetchone()
        if not exists:
            _insert_quiz(conn, quiz, None)
            added["quizzes"] += 1
    conn.commit()
    return added


def main(argv: list[str]) -> None:  # pragma: no cover - thin CLI wrapper
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT_FILE
    data = json.loads(path.read_text(encoding="utf-8"))
    conn = get_connection(get_settings().db_path)
    init_db(conn)
    added = seed(conn, data)
    print(
        f"Добавлено: тем — {added['topics']}, уроков — {added['lessons']}, квизов — {added['quizzes']}"
    )


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv)

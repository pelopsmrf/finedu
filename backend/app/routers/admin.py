import json
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.converters import row_to_lesson, row_to_quiz, row_to_topic
from app.db import get_db
from app.notifications import broadcast as send_broadcast
from app.schemas import (
    BroadcastIn,
    Lesson,
    LessonCreate,
    Quiz,
    QuizCreate,
    Topic,
    TopicCreate,
)
from app.telegram_auth import require_admin

router = APIRouter(prefix="/api/admin")


def _dump(items) -> str:
    return json.dumps([i.model_dump(exclude_none=True) for i in items], ensure_ascii=False)


def _require_row(conn: sqlite3.Connection, table: str, row_id: int, name: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"{name} not found")
    return row


def _delete_lessons(conn: sqlite3.Connection, where: str, params: tuple) -> None:
    """Delete lessons matching `where` together with their quizzes."""
    conn.execute(
        f"DELETE FROM quizzes WHERE lesson_id IN (SELECT id FROM lessons WHERE {where})", params
    )
    conn.execute(f"DELETE FROM lessons WHERE {where}", params)


@router.get("/_probe")
def probe(user: dict = Depends(require_admin)) -> dict:
    return {"ok": True}


# --- Topics -----------------------------------------------------------------


@router.get("/topics", response_model=list[Topic])
def list_topics(
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
):
    rows = conn.execute('SELECT * FROM topics ORDER BY "order", id').fetchall()
    return [row_to_topic(r) for r in rows]


@router.get("/topics/{topic_id}", response_model=Topic)
def get_topic(
    topic_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return row_to_topic(_require_row(conn, "topics", topic_id, "Topic"))


@router.post("/topics", response_model=Topic)
def create_topic(
    payload: TopicCreate,
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> Topic:
    cur = conn.execute(
        'INSERT INTO topics (title, description, icon, "order", is_published) '
        "VALUES (?, ?, ?, ?, ?)",
        (
            payload.title,
            payload.description,
            payload.icon,
            payload.order,
            int(payload.is_published),
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM topics WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_topic(row)


@router.put("/topics/{topic_id}", response_model=Topic)
def update_topic(
    topic_id: int,
    payload: TopicCreate,
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> Topic:
    _require_row(conn, "topics", topic_id, "Topic")
    conn.execute(
        'UPDATE topics SET title=?, description=?, icon=?, "order"=?, is_published=? '
        "WHERE id=?",
        (
            payload.title,
            payload.description,
            payload.icon,
            payload.order,
            int(payload.is_published),
            topic_id,
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM topics WHERE id = ?", (topic_id,)).fetchone()
    return row_to_topic(row)


@router.delete("/topics/{topic_id}")
def delete_topic(
    topic_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> dict:
    _delete_lessons(conn, "topic_id = ?", (topic_id,))
    conn.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
    conn.commit()
    return {"deleted": True}


# --- Lessons -----------------------------------------------------------------


@router.get("/topics/{topic_id}/lessons", response_model=list[Lesson])
def list_topic_lessons(
    topic_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
):
    rows = conn.execute(
        'SELECT * FROM lessons WHERE topic_id = ? ORDER BY "order", id', (topic_id,)
    ).fetchall()
    return [lesson for lesson in map(row_to_lesson, rows) if lesson is not None]


@router.get("/lessons/{lesson_id}", response_model=Lesson)
def get_lesson(
    lesson_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
):
    lesson = row_to_lesson(_require_row(conn, "lessons", lesson_id, "Lesson"))
    if lesson is None:
        raise HTTPException(status_code=500, detail="Lesson content is corrupted")
    return lesson


@router.post("/lessons", response_model=Lesson)
def create_lesson(
    payload: LessonCreate,
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> Lesson:
    _require_row(conn, "topics", payload.topic_id, "Topic")
    cur = conn.execute(
        'INSERT INTO lessons (topic_id, title, "order", content, is_published) '
        "VALUES (?, ?, ?, ?, ?)",
        (
            payload.topic_id,
            payload.title,
            payload.order,
            _dump(payload.content),
            int(payload.is_published),
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM lessons WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_lesson(row)


@router.put("/lessons/{lesson_id}", response_model=Lesson)
def update_lesson(
    lesson_id: int,
    payload: LessonCreate,
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> Lesson:
    _require_row(conn, "lessons", lesson_id, "Lesson")
    _require_row(conn, "topics", payload.topic_id, "Topic")
    conn.execute(
        'UPDATE lessons SET topic_id=?, title=?, "order"=?, content=?, is_published=? '
        "WHERE id=?",
        (
            payload.topic_id,
            payload.title,
            payload.order,
            _dump(payload.content),
            int(payload.is_published),
            lesson_id,
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
    return row_to_lesson(row)


@router.delete("/lessons/{lesson_id}")
def delete_lesson(
    lesson_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> dict:
    _delete_lessons(conn, "id = ?", (lesson_id,))
    conn.commit()
    return {"deleted": True}


# --- Quizzes -----------------------------------------------------------------


@router.get("/quizzes", response_model=list[Quiz])
def list_quizzes(
    lesson_id: int | None = None,
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """All quizzes; `?lesson_id=N` narrows to one lesson's quizzes."""
    if lesson_id is None:
        rows = conn.execute("SELECT * FROM quizzes ORDER BY id").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM quizzes WHERE lesson_id = ? ORDER BY id", (lesson_id,)
        ).fetchall()
    return [quiz for quiz in map(row_to_quiz, rows) if quiz is not None]


@router.get("/quizzes/{quiz_id}", response_model=Quiz)
def get_quiz(
    quiz_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
):
    quiz = row_to_quiz(_require_row(conn, "quizzes", quiz_id, "Quiz"))
    if quiz is None:
        raise HTTPException(status_code=500, detail="Quiz questions are corrupted")
    return quiz


@router.post("/quizzes", response_model=Quiz)
def create_quiz(
    payload: QuizCreate,
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> Quiz:
    if payload.lesson_id is not None:
        _require_row(conn, "lessons", payload.lesson_id, "Lesson")
    cur = conn.execute(
        "INSERT INTO quizzes (lesson_id, title, questions, is_published) "
        "VALUES (?, ?, ?, ?)",
        (
            payload.lesson_id,
            payload.title,
            _dump(payload.questions),
            int(payload.is_published),
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM quizzes WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_quiz(row)


@router.put("/quizzes/{quiz_id}", response_model=Quiz)
def update_quiz(
    quiz_id: int,
    payload: QuizCreate,
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> Quiz:
    _require_row(conn, "quizzes", quiz_id, "Quiz")
    if payload.lesson_id is not None:
        _require_row(conn, "lessons", payload.lesson_id, "Lesson")
    conn.execute(
        "UPDATE quizzes SET lesson_id=?, title=?, questions=?, is_published=? WHERE id=?",
        (
            payload.lesson_id,
            payload.title,
            _dump(payload.questions),
            int(payload.is_published),
            quiz_id,
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,)).fetchone()
    return row_to_quiz(row)


@router.delete("/quizzes/{quiz_id}")
def delete_quiz(
    quiz_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> dict:
    conn.execute("DELETE FROM quizzes WHERE id = ?", (quiz_id,))
    conn.commit()
    return {"deleted": True}


# --- Broadcast ----------------------------------------------------------------


@router.post("/broadcast")
def broadcast_endpoint(
    payload: BroadcastIn,
    conn: sqlite3.Connection = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: dict = Depends(require_admin),
) -> dict:
    sent = send_broadcast(conn, settings, payload.text, payload.only_inactive_days)
    return {"sent": sent}


# --- Stats -------------------------------------------------------------------


@router.get("/stats")
def stats(
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> dict:
    rows = conn.execute(
        "SELECT l.topic_id AS topic_id, COUNT(DISTINCT p.telegram_id) AS completed_count "
        "FROM progress p "
        "JOIN lessons l ON l.id = p.lesson_id "
        "WHERE p.completed_at IS NOT NULL "
        "GROUP BY l.topic_id"
    ).fetchall()
    return {str(r["topic_id"]): {"completed_count": r["completed_count"]} for r in rows}

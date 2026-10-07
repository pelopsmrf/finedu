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


@router.get("/_probe")
def probe(user: dict = Depends(require_admin)) -> dict:
    return {"ok": True}


# --- Topics -----------------------------------------------------------------


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
    existing = conn.execute("SELECT id FROM topics WHERE id = ?", (topic_id,)).fetchone()
    if existing is None:
        raise HTTPException(status_code=404, detail="Topic not found")
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
    conn.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
    conn.commit()
    return {"deleted": True}


# --- Lessons -----------------------------------------------------------------


@router.post("/lessons", response_model=Lesson)
def create_lesson(
    payload: LessonCreate,
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> Lesson:
    cur = conn.execute(
        'INSERT INTO lessons (topic_id, title, "order", content, is_published) '
        "VALUES (?, ?, ?, ?, ?)",
        (
            payload.topic_id,
            payload.title,
            payload.order,
            json.dumps(payload.content),
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
    existing = conn.execute("SELECT id FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
    if existing is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    conn.execute(
        'UPDATE lessons SET topic_id=?, title=?, "order"=?, content=?, is_published=? '
        "WHERE id=?",
        (
            payload.topic_id,
            payload.title,
            payload.order,
            json.dumps(payload.content),
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
    conn.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
    conn.commit()
    return {"deleted": True}


# --- Quizzes -----------------------------------------------------------------


@router.post("/quizzes", response_model=Quiz)
def create_quiz(
    payload: QuizCreate,
    conn: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> Quiz:
    cur = conn.execute(
        "INSERT INTO quizzes (lesson_id, title, questions, is_published) "
        "VALUES (?, ?, ?, ?)",
        (
            payload.lesson_id,
            payload.title,
            json.dumps(payload.questions),
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
    existing = conn.execute("SELECT id FROM quizzes WHERE id = ?", (quiz_id,)).fetchone()
    if existing is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    conn.execute(
        "UPDATE quizzes SET lesson_id=?, title=?, questions=?, is_published=? WHERE id=?",
        (
            payload.lesson_id,
            payload.title,
            json.dumps(payload.questions),
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

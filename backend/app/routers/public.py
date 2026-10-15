import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.converters import row_to_lesson, row_to_quiz, row_to_topic
from app.db import get_db
from app.schemas import Lesson, Quiz, Topic

router = APIRouter(prefix="/api")

# A lesson is visible only if both the lesson and its topic are published.
VISIBLE_LESSON = (
    "SELECT l.* FROM lessons l JOIN topics t ON t.id = l.topic_id "
    "WHERE l.is_published = 1 AND t.is_published = 1"
)
# A quiz is visible if it is published and either standalone or attached to a visible lesson.
VISIBLE_QUIZ = (
    "SELECT q.* FROM quizzes q WHERE q.is_published = 1 AND ("
    f"q.lesson_id IS NULL OR q.lesson_id IN (SELECT id FROM ({VISIBLE_LESSON})))"
)


@router.get("/topics", response_model=list[Topic])
def list_topics(conn: sqlite3.Connection = Depends(get_db)):
    rows = conn.execute(
        'SELECT * FROM topics WHERE is_published = 1 ORDER BY "order", id'
    ).fetchall()
    return [row_to_topic(r) for r in rows]


@router.get("/topics/{topic_id}", response_model=Topic)
def get_topic(topic_id: int, conn: sqlite3.Connection = Depends(get_db)):
    row = conn.execute(
        "SELECT * FROM topics WHERE id = ? AND is_published = 1", (topic_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return row_to_topic(row)


@router.get("/topics/{topic_id}/lessons", response_model=list[Lesson])
def list_topic_lessons(topic_id: int, conn: sqlite3.Connection = Depends(get_db)):
    rows = conn.execute(
        f'{VISIBLE_LESSON} AND l.topic_id = ? ORDER BY l."order", l.id',
        (topic_id,),
    ).fetchall()
    lessons = [row_to_lesson(r) for r in rows]
    return [lesson for lesson in lessons if lesson is not None]


@router.get("/lessons/{lesson_id}", response_model=Lesson)
def get_lesson(lesson_id: int, conn: sqlite3.Connection = Depends(get_db)):
    row = conn.execute(f"{VISIBLE_LESSON} AND l.id = ?", (lesson_id,)).fetchone()
    lesson = row_to_lesson(row) if row is not None else None
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.get("/lessons/{lesson_id}/quiz", response_model=Quiz)
def get_lesson_quiz(lesson_id: int, conn: sqlite3.Connection = Depends(get_db)):
    """The quiz shown right after the lesson (the first published one, if several)."""
    rows = conn.execute(
        f"{VISIBLE_QUIZ} AND q.lesson_id = ? ORDER BY q.id", (lesson_id,)
    ).fetchall()
    for row in rows:
        quiz = row_to_quiz(row)
        if quiz is not None and quiz.questions:
            return quiz
    raise HTTPException(status_code=404, detail="Quiz not found")


@router.get("/quizzes", response_model=list[Quiz])
def list_quizzes(conn: sqlite3.Connection = Depends(get_db)):
    rows = conn.execute(f"{VISIBLE_QUIZ} AND q.lesson_id IS NULL ORDER BY q.id").fetchall()
    quizzes = [row_to_quiz(r) for r in rows]
    return [quiz for quiz in quizzes if quiz is not None]


@router.get("/quizzes/{quiz_id}", response_model=Quiz)
def get_quiz(quiz_id: int, conn: sqlite3.Connection = Depends(get_db)):
    row = conn.execute(f"{VISIBLE_QUIZ} AND q.id = ?", (quiz_id,)).fetchone()
    quiz = row_to_quiz(row) if row is not None else None
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz

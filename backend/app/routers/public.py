import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.converters import row_to_lesson, row_to_quiz, row_to_topic
from app.db import get_db
from app.schemas import Lesson, Quiz, Topic

router = APIRouter(prefix="/api")


@router.get("/topics", response_model=list[Topic])
def list_topics(conn: sqlite3.Connection = Depends(get_db)):
    rows = conn.execute(
        'SELECT * FROM topics WHERE is_published = 1 ORDER BY "order"'
    ).fetchall()
    return [row_to_topic(r) for r in rows]


@router.get("/topics/{topic_id}/lessons", response_model=list[Lesson])
def list_topic_lessons(topic_id: int, conn: sqlite3.Connection = Depends(get_db)):
    rows = conn.execute(
        'SELECT * FROM lessons WHERE topic_id = ? AND is_published = 1 ORDER BY "order"',
        (topic_id,),
    ).fetchall()
    lessons = [row_to_lesson(r) for r in rows]
    return [lesson for lesson in lessons if lesson is not None]


@router.get("/lessons/{lesson_id}", response_model=Lesson)
def get_lesson(lesson_id: int, conn: sqlite3.Connection = Depends(get_db)):
    row = conn.execute(
        "SELECT * FROM lessons WHERE id = ? AND is_published = 1", (lesson_id,)
    ).fetchone()
    lesson = row_to_lesson(row) if row is not None else None
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.get("/quizzes", response_model=list[Quiz])
def list_quizzes(conn: sqlite3.Connection = Depends(get_db)):
    rows = conn.execute(
        "SELECT * FROM quizzes WHERE lesson_id IS NULL AND is_published = 1"
    ).fetchall()
    quizzes = [row_to_quiz(r) for r in rows]
    return [quiz for quiz in quizzes if quiz is not None]


@router.get("/quizzes/{quiz_id}", response_model=Quiz)
def get_quiz(quiz_id: int, conn: sqlite3.Connection = Depends(get_db)):
    row = conn.execute(
        "SELECT * FROM quizzes WHERE id = ? AND is_published = 1", (quiz_id,)
    ).fetchone()
    quiz = row_to_quiz(row) if row is not None else None
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz

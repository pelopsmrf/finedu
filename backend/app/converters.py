import json
import sqlite3

from app.schemas import Lesson, Quiz, Topic


def row_to_topic(row: sqlite3.Row) -> Topic:
    return Topic(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        icon=row["icon"],
        order=row["order"],
        is_published=bool(row["is_published"]),
    )


def row_to_lesson(row: sqlite3.Row) -> Lesson | None:
    try:
        content = json.loads(row["content"])
    except (ValueError, TypeError):
        return None
    return Lesson(
        id=row["id"],
        topic_id=row["topic_id"],
        title=row["title"],
        order=row["order"],
        content=content,
        is_published=bool(row["is_published"]),
    )


def row_to_quiz(row: sqlite3.Row) -> Quiz | None:
    try:
        questions = json.loads(row["questions"])
    except (ValueError, TypeError):
        return None
    return Quiz(
        id=row["id"],
        lesson_id=row["lesson_id"],
        title=row["title"],
        questions=questions,
        is_published=bool(row["is_published"]),
    )

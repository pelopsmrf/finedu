"""Per-topic progress and badges, computed from the progress table on the fly.

Badges are not stored: they follow from what the user has already done, so users
who studied before badges existed get them right away.
"""

import json
import sqlite3
from datetime import date, datetime, timedelta, timezone

# Russia has no daylight saving time, so a fixed offset is exact.
MOSCOW = timezone(timedelta(hours=3))

STREAK_DAYS = 3
QUIZ_COUNT = 5

BADGES = [
    {"id": "first_lesson", "icon": "🌱", "title": "Первый шаг",
     "description": "Пройди первый урок"},
    {"id": "topic_done", "icon": "📚", "title": "Знаток темы",
     "description": "Пройди все уроки одной темы"},
    {"id": "perfect_quiz", "icon": "🎯", "title": "Без ошибок",
     "description": "Реши квиз без единой ошибки"},
    {"id": "five_quizzes", "icon": "🧠", "title": "Пять квизов",
     "description": f"Реши {QUIZ_COUNT} разных квизов"},
    {"id": "streak_3", "icon": "🔥", "title": "Три дня подряд",
     "description": f"Занимайся {STREAK_DAYS} дня подряд"},
    {"id": "all_done", "icon": "🏆", "title": "Всё пройдено",
     "description": "Пройди все уроки приложения"},
]


def topic_progress(conn: sqlite3.Connection, completed_lesson_ids: set[int]) -> list[dict]:
    """Published topics with the number of their published lessons the user completed."""
    rows = conn.execute(
        'SELECT t.id, t.title, t.icon, l.id AS lesson_id FROM topics t '
        "LEFT JOIN lessons l ON l.topic_id = t.id AND l.is_published = 1 "
        'WHERE t.is_published = 1 ORDER BY t."order", t.id'
    ).fetchall()
    topics: dict[int, dict] = {}
    for r in rows:
        topic = topics.setdefault(
            r["id"],
            {"topic_id": r["id"], "title": r["title"], "icon": r["icon"],
             "completed": 0, "total": 0},
        )
        if r["lesson_id"] is not None:
            topic["total"] += 1
            if r["lesson_id"] in completed_lesson_ids:
                topic["completed"] += 1
    return list(topics.values())


def _longest_streak(days: set[date]) -> int:
    best = 0
    for day in days:
        if day - timedelta(days=1) in days:
            continue  # not the start of a run
        length = 1
        while day + timedelta(days=length) in days:
            length += 1
        best = max(best, length)
    return best


def _activity_days(rows: list[sqlite3.Row]) -> set[date]:
    days = set()
    for r in rows:
        if r["last_activity_at"]:
            moment = datetime.fromisoformat(r["last_activity_at"])
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=timezone.utc)
            days.add(moment.astimezone(MOSCOW).date())
    return days


def _perfect_quiz(conn: sqlite3.Connection, rows: list[sqlite3.Row]) -> bool:
    best: dict[int, int] = {}
    for r in rows:
        if r["quiz_id"] is not None and r["quiz_score"] is not None:
            best[r["quiz_id"]] = max(best.get(r["quiz_id"], 0), r["quiz_score"])
    if not best:
        return False
    marks = ",".join("?" * len(best))
    quizzes = conn.execute(
        f"SELECT id, questions FROM quizzes WHERE id IN ({marks})", list(best)
    ).fetchall()
    for q in quizzes:
        total = len(json.loads(q["questions"] or "[]"))
        if total > 0 and best[q["id"]] >= total:
            return True
    return False


def summarize(conn: sqlite3.Connection, telegram_id: int) -> dict:
    """Everything the progress screen needs: totals, per-topic progress, badges."""
    rows = conn.execute(
        "SELECT lesson_id, completed_at, quiz_id, quiz_score, last_activity_at "
        "FROM progress WHERE telegram_id = ?",
        (telegram_id,),
    ).fetchall()
    completed_ids = {
        r["lesson_id"] for r in rows if r["lesson_id"] is not None and r["completed_at"]
    }
    topics = topic_progress(conn, completed_ids)
    completed = sum(t["completed"] for t in topics)
    total = sum(t["total"] for t in topics)

    earned = {
        "first_lesson": completed > 0,
        "topic_done": any(t["total"] > 0 and t["completed"] == t["total"] for t in topics),
        "perfect_quiz": _perfect_quiz(conn, rows),
        "five_quizzes": len({r["quiz_id"] for r in rows if r["quiz_id"] is not None})
        >= QUIZ_COUNT,
        "streak_3": _longest_streak(_activity_days(rows)) >= STREAK_DAYS,
        "all_done": total > 0 and completed == total,
    }
    return {
        "progress": [dict(r) for r in rows],
        "completed_lessons": completed,
        "total_lessons": total,
        "topics": topics,
        "badges": [{**b, "earned": earned[b["id"]]} for b in BADGES],
    }


def earned_badge_ids(conn: sqlite3.Connection, telegram_id: int) -> set[str]:
    return {b["id"] for b in summarize(conn, telegram_id)["badges"] if b["earned"]}

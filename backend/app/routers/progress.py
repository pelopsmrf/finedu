import sqlite3
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.db import delete_user_data, ensure_user, get_db
from app.schemas import ProgressIn, ProgressOut
from app.telegram_auth import require_verified_user

router = APIRouter(prefix="/api")


@router.post("/progress", response_model=ProgressOut)
def submit_progress(
    payload: ProgressIn,
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(require_verified_user),
) -> ProgressOut:
    telegram_id = user["id"]
    now = datetime.now(timezone.utc).isoformat()
    ensure_user(conn, telegram_id, now)
    completed_at = now if payload.lesson_id is not None else None
    conn.execute(
        "INSERT INTO progress "
        "(telegram_id, lesson_id, completed_at, quiz_id, quiz_score, last_activity_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            telegram_id,
            payload.lesson_id,
            completed_at,
            payload.quiz_id,
            payload.quiz_score,
            now,
        ),
    )
    conn.commit()
    return ProgressOut(
        lesson_id=payload.lesson_id,
        quiz_id=payload.quiz_id,
        quiz_score=payload.quiz_score,
        completed_at=completed_at,
        last_activity_at=now,
    )


@router.get("/progress/me")
def get_my_progress(
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(require_verified_user),
) -> dict:
    telegram_id = user["id"]
    rows = conn.execute(
        "SELECT lesson_id, completed_at, quiz_id, quiz_score, last_activity_at "
        "FROM progress WHERE telegram_id = ?",
        (telegram_id,),
    ).fetchall()
    completed_lessons = len(
        {r["lesson_id"] for r in rows if r["lesson_id"] is not None and r["completed_at"]}
    )
    total_lessons = conn.execute(
        "SELECT COUNT(*) FROM lessons WHERE is_published = 1"
    ).fetchone()[0]
    return {
        "progress": [dict(r) for r in rows],
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
    }


@router.delete("/users/me")
def delete_my_data(
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(require_verified_user),
) -> dict:
    delete_user_data(conn, user["id"])
    return {"deleted": True}

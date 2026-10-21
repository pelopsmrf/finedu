import sqlite3
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.achievements import BADGES, earned_badge_ids, summarize
from app.db import delete_user_data, ensure_user, get_db, set_notifications
from app.schemas import NotificationsIn, ProgressIn, ProgressOut
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
    badges_before = earned_badge_ids(conn, telegram_id)
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
    badges_after = earned_badge_ids(conn, telegram_id)
    return ProgressOut(
        lesson_id=payload.lesson_id,
        quiz_id=payload.quiz_id,
        quiz_score=payload.quiz_score,
        completed_at=completed_at,
        last_activity_at=now,
        new_badges=[b for b in BADGES if b["id"] in badges_after - badges_before],
    )


@router.get("/progress/me")
def get_my_progress(
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(require_verified_user),
) -> dict:
    return summarize(conn, user["id"])


@router.delete("/users/me")
def delete_my_data(
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(require_verified_user),
) -> dict:
    delete_user_data(conn, user["id"])
    return {"deleted": True}


def _notifications_state(conn: sqlite3.Connection, telegram_id: int) -> dict:
    ensure_user(conn, telegram_id, datetime.now(timezone.utc).isoformat())
    row = conn.execute(
        "SELECT notifications_enabled FROM users WHERE telegram_id = ?", (telegram_id,)
    ).fetchone()
    return {"enabled": bool(row["notifications_enabled"])}


@router.get("/users/me/notifications")
def get_my_notifications(
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(require_verified_user),
) -> dict:
    return _notifications_state(conn, user["id"])


@router.put("/users/me/notifications")
def set_my_notifications(
    payload: NotificationsIn,
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(require_verified_user),
) -> dict:
    ensure_user(conn, user["id"], datetime.now(timezone.utc).isoformat())
    set_notifications(conn, user["id"], payload.enabled)
    return _notifications_state(conn, user["id"])

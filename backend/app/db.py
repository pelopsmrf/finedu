import sqlite3

from app.config import get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    "order" INTEGER NOT NULL DEFAULT 0,
    is_published INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL REFERENCES topics(id),
    title TEXT NOT NULL,
    "order" INTEGER NOT NULL DEFAULT 0,
    content TEXT NOT NULL DEFAULT '[]',
    is_published INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_lessons_topic_id ON lessons(topic_id);

CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER REFERENCES lessons(id),
    title TEXT NOT NULL,
    questions TEXT NOT NULL DEFAULT '[]',
    is_published INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    lesson_id INTEGER,
    completed_at TEXT,
    quiz_id INTEGER,
    quiz_score INTEGER,
    last_activity_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_progress_telegram_id ON progress(telegram_id);

CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL,
    notifications_enabled INTEGER NOT NULL DEFAULT 1,
    last_reminded_at TEXT
);
"""

# Columns added after the first release: (table, column, SQL type).
# CREATE TABLE IF NOT EXISTS does not touch existing tables, so they are added here.
MIGRATIONS = [
    ("users", "last_reminded_at", "TEXT"),
]


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    for table, column, sql_type in MIGRATIONS:
        existing = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}")
    conn.commit()


def ensure_user(conn: sqlite3.Connection, telegram_id: int, now: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO users (telegram_id, created_at, notifications_enabled) "
        "VALUES (?, ?, 1)",
        (telegram_id, now),
    )
    conn.commit()


def delete_user_data(conn: sqlite3.Connection, telegram_id: int) -> None:
    conn.execute("DELETE FROM progress WHERE telegram_id = ?", (telegram_id,))
    conn.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
    conn.commit()


def set_notifications(conn: sqlite3.Connection, telegram_id: int, enabled: bool) -> None:
    conn.execute(
        "UPDATE users SET notifications_enabled = ? WHERE telegram_id = ?",
        (int(enabled), telegram_id),
    )
    conn.commit()


def get_db():
    settings = get_settings()
    conn = get_connection(settings.db_path)
    init_db(conn)
    try:
        yield conn
    finally:
        conn.close()

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
    notifications_enabled INTEGER NOT NULL DEFAULT 1
);
"""


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def get_db():
    settings = get_settings()
    conn = get_connection(settings.db_path)
    init_db(conn)
    try:
        yield conn
    finally:
        conn.close()

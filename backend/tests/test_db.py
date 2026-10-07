from app.db import get_connection, init_db


def test_init_db_creates_all_tables(tmp_path):
    conn = get_connection(str(tmp_path / "test.db"))
    init_db(conn)
    tables = {
        r[0]
        for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {"topics", "lessons", "quizzes", "progress", "users"} <= tables

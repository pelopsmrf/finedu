"""Standalone script to send inactivity reminders. Run via cron:
    python -m app.scripts.send_reminders
"""

from app.config import get_settings
from app.db import get_connection, init_db
from app.notifications import send_reminders


def main() -> int:
    settings = get_settings()
    conn = get_connection(settings.db_path)
    init_db(conn)
    sent = send_reminders(conn, settings)
    print(f"Sent {sent} reminder(s)")
    return sent


if __name__ == "__main__":  # pragma: no cover
    main()

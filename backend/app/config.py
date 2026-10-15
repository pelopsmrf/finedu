import os
from functools import lru_cache

from pydantic import BaseModel

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is in requirements.txt
    load_dotenv = None

# Admin token shorter than this is ignored, so a typo like "123" can't open the admin panel.
MIN_ADMIN_TOKEN_LENGTH = 32


class Settings(BaseModel):
    bot_token: str
    admin_id: int
    db_path: str
    reminder_days: int = 3
    init_data_max_age_seconds: int = 86400
    admin_token: str | None = None
    webapp_url: str = "https://moneyedu.ru"


@lru_cache
def get_settings() -> Settings:
    if load_dotenv is not None:
        # Local runs read backend/.env; on the server systemd's EnvironmentFile wins.
        load_dotenv(override=False)
    return Settings(
        bot_token=os.environ["FINEDU_BOT_TOKEN"],
        admin_id=int(os.environ["FINEDU_ADMIN_ID"]),
        db_path=os.environ["FINEDU_DB_PATH"],
        admin_token=os.environ.get("FINEDU_ADMIN_TOKEN") or None,
        webapp_url=os.environ.get("FINEDU_WEBAPP_URL", "https://moneyedu.ru").rstrip("/"),
    )

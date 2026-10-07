import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    bot_token: str
    admin_id: int
    db_path: str
    reminder_days: int = 3
    init_data_max_age_seconds: int = 86400


@lru_cache
def get_settings() -> Settings:
    return Settings(
        bot_token=os.environ["FINEDU_BOT_TOKEN"],
        admin_id=int(os.environ["FINEDU_ADMIN_ID"]),
        db_path=os.environ["FINEDU_DB_PATH"],
    )

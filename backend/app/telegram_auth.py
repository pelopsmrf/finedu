import hashlib
import hmac
import json
import time
import urllib.parse

from fastapi import Depends, Header, HTTPException

from app.config import Settings, get_settings


def verify_init_data(init_data: str, bot_token: str, max_age_seconds: int) -> dict | None:
    """Verify Telegram WebApp initData per Telegram's documented algorithm.

    Returns the parsed fields (including a decoded `user` dict) if the HMAC
    signature is valid and `auth_date` is within `max_age_seconds` of now.
    Returns None on any failure to parse, verify, or freshness check.
    """
    if not init_data:
        return None
    try:
        pairs = dict(urllib.parse.parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    auth_date = pairs.get("auth_date")
    if auth_date is None:
        return None
    try:
        auth_date_ts = int(auth_date)
    except ValueError:
        return None
    if time.time() - auth_date_ts > max_age_seconds:
        return None

    result = dict(pairs)
    user_raw = pairs.get("user")
    if user_raw:
        try:
            result["user"] = json.loads(user_raw)
        except ValueError:
            return None
    return result


def require_verified_user(
    x_telegram_init_data: str = Header(default=""),
    settings: Settings = Depends(get_settings),
) -> dict:
    data = verify_init_data(
        x_telegram_init_data, settings.bot_token, settings.init_data_max_age_seconds
    )
    if not data or "user" not in data or "id" not in data["user"]:
        raise HTTPException(status_code=403, detail="Invalid Telegram initData")
    return data["user"]


def require_admin(
    user: dict = Depends(require_verified_user),
    settings: Settings = Depends(get_settings),
) -> dict:
    if user["id"] != settings.admin_id:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

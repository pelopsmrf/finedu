import hashlib
import hmac
import json
import time
import urllib.parse

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def make_init_data():
    def _make(user_id, bot_token, tamper=False, auth_date_offset_seconds=0):
        auth_date = int(time.time()) + auth_date_offset_seconds
        user_json = json.dumps({"id": user_id, "first_name": "Test"})
        pairs = {
            "auth_date": str(auth_date),
            "query_id": "AAFtest",
            "user": user_json,
        }
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        computed_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()
        if tamper:
            flipped = "1" if computed_hash[0] != "1" else "2"
            computed_hash = flipped + computed_hash[1:]
        all_pairs = dict(pairs)
        all_pairs["hash"] = computed_hash
        return urllib.parse.urlencode(all_pairs)

    return _make

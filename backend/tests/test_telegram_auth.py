import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.telegram_auth import require_admin, verify_init_data

ADMIN_ID = 777
TEST_BOT_TOKEN = "test-bot-token"  # noqa: S105 - test fixture only


def _test_settings() -> Settings:
    return Settings(bot_token=TEST_BOT_TOKEN, admin_id=ADMIN_ID, db_path=":memory:")


probe_app = FastAPI()
probe_app.dependency_overrides[get_settings] = _test_settings


@probe_app.get("/api/admin/_probe")
def probe(user: dict = Depends(require_admin)):
    return {"ok": True}


@pytest.fixture
def client():
    return TestClient(probe_app)


def test_rejects_missing_init_data(client):
    resp = client.get("/api/admin/_probe")
    assert resp.status_code in (401, 403)


def test_rejects_tampered_signature(client, make_init_data):
    bad = make_init_data(user_id=ADMIN_ID, bot_token=TEST_BOT_TOKEN, tamper=True)
    resp = client.get("/api/admin/_probe", headers={"X-Telegram-Init-Data": bad})
    assert resp.status_code == 403


def test_rejects_valid_signature_wrong_user(client, make_init_data):
    data = make_init_data(user_id=ADMIN_ID + 1, bot_token=TEST_BOT_TOKEN, tamper=False)
    resp = client.get("/api/admin/_probe", headers={"X-Telegram-Init-Data": data})
    assert resp.status_code == 403


def test_accepts_valid_signature_admin_user(client, make_init_data):
    data = make_init_data(user_id=ADMIN_ID, bot_token=TEST_BOT_TOKEN, tamper=False)
    resp = client.get("/api/admin/_probe", headers={"X-Telegram-Init-Data": data})
    assert resp.status_code == 200


def test_rejects_stale_init_data(make_init_data):
    old = make_init_data(
        user_id=ADMIN_ID, bot_token=TEST_BOT_TOKEN, auth_date_offset_seconds=-90000
    )
    assert verify_init_data(old, TEST_BOT_TOKEN, max_age_seconds=86400) is None

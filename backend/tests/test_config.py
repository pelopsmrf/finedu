from app.config import get_settings


def test_get_settings_reads_env(monkeypatch):
    monkeypatch.setenv("FINEDU_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("FINEDU_ADMIN_ID", "42")
    monkeypatch.setenv("FINEDU_DB_PATH", "/tmp/finedu-test.db")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.bot_token == "123:abc"
    assert settings.admin_id == 42
    assert settings.db_path == "/tmp/finedu-test.db"
    assert settings.reminder_days == 3
    assert settings.init_data_max_age_seconds == 86400

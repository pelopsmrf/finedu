# Finedu

Telegram Mini App по финансовой грамотности для старшеклассников и студентов:
темы → уроки-карточки → квизы, прогресс, напоминания от бота.
Открывается и в обычном браузере (без сохранения прогресса).

- `backend/` — FastAPI + SQLite, бот (`app/scripts/bot.py`), напоминания
  (`app/scripts/send_reminders.py`), загрузка контента (`app/scripts/seed_content.py`).
- `backend/content/starter.json` — стартовые темы, уроки и квизы.
- `frontend/` — React + Vite; админка по адресу `/admin`.
- `docs/deploy.md` — установка на сервер, обновление, локальный запуск.
- `docs/superpowers/specs/` — исходная спецификация.

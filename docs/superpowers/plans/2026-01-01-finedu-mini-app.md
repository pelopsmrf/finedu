# Finedu Telegram Mini App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Telegram Mini App (works in Telegram and in a plain
browser) that teaches financial literacy through topics → lessons → quizzes,
with Telegram-only progress tracking, a signature-protected admin panel, and
reminder/broadcast notifications.

**Architecture:** One FastAPI process serves both a JSON API and the built
React static frontend. SQLite is the only datastore. A small notifications
module (callable from a cron-style script or the admin broadcast endpoint)
sends Telegram messages. All admin and progress endpoints trust `telegram_id`
only after verifying Telegram's `initData` HMAC signature server-side —
never from request bodies.

**Tech Stack:** Python 3.11+, FastAPI, `sqlite3` (standard library), Pydantic,
`httpx` (outbound Telegram API calls + testable in-process), `pytest`;
React + Vite + React Router (frontend), `vitest` for pure-logic unit tests.

**Spec:** `docs/superpowers/specs/2026-01-01-finedu-mini-app-design.md`

## Global Constraints

- Only `telegram_id` is stored for users — no names, phones, emails (spec §6, §11).
- Admin and progress endpoints must derive `telegram_id` exclusively from a
  cryptographically verified `initData`, never from the request body (spec §7, §8).
- `BOT_TOKEN` and `ADMIN_ID` live only in a server-side `.env`/config file,
  never in code or git history (spec §12).
- Data store is SQLite only; no ORM, no message queue, no Docker (spec §5).
- Interface language: Russian only (spec §13).
- Bottom nav is exactly 4 tabs, fixed order: Темы (default), Квизы, Прогресс,
  О проекте (spec §3).
- Browser (non-Telegram) mode is read-only: no progress saved (spec §2).
- 4 mandatory security tests proving admin access fails without a valid
  signature (spec §8) must exist and pass before deploy is considered done.

## Review Focus

- **Admin/progress request with a syntactically valid but admin-irrelevant
  `initData`** (e.g. missing `user` field entirely) — must return 403, not a
  500 from a `KeyError`. Covered in Task 3.
- **Browser calls a Telegram-only endpoint with no `initData` header at all**
  — must return a clean 401/403, not crash. Covered in Task 3 and Task 5.
- **Quiz row with malformed/empty `questions` JSON in the database** — the
  public API must skip or safely report it, not throw an unhandled
  exception. Covered in Task 4.
- **Replayed/stale `initData`** (captured once, reused indefinitely) — verify
  `auth_date` is within a bounded freshness window (24h) in addition to the
  signature check. Covered in Task 3.
- **Broadcast to zero matching inactive users** — admin broadcast endpoint
  must respond with a success count of 0, not an error. Covered in Task 7.

---

## Backend

### Task 1: Backend scaffolding and configuration

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/main.py`
- Test: `backend/tests/test_config.py`
- Test: `backend/tests/test_health.py`

**Interfaces:**
- Produces: `config.Settings` (Pydantic model: `bot_token: str`,
  `admin_id: int`, `db_path: str`, `reminder_days: int = 3`,
  `init_data_max_age_seconds: int = 86400`) and `config.get_settings() ->
  Settings`, reading from environment variables
  `FINEDU_BOT_TOKEN`, `FINEDU_ADMIN_ID`, `FINEDU_DB_PATH`.
- Produces: `app.main.app` — a FastAPI instance with `GET /api/health`
  returning `{"status": "ok"}`.

- [ ] **Step 1: Write failing test for `get_settings()`**

```python
def test_get_settings_reads_env(monkeypatch):
    monkeypatch.setenv("FINEDU_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("FINEDU_ADMIN_ID", "42")
    monkeypatch.setenv("FINEDU_DB_PATH", "/tmp/finedu-test.db")
    settings = get_settings()
    assert settings.bot_token == "123:abc"
    assert settings.admin_id == 42
    assert settings.reminder_days == 3
```

- [ ] **Step 2: Run test, verify it fails** (`pytest backend/tests/test_config.py -v`, expect ImportError/fail)
- [ ] **Step 3: Implement `config.py` per the Interfaces block above**
- [ ] **Step 4: Run test, verify it passes**
- [ ] **Step 5: Write failing test for health check**

```python
def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Step 6: Run test, verify it fails**
- [ ] **Step 7: Implement `main.py`** — create FastAPI app, add `/api/health`.
  Add `backend/requirements.txt` (fastapi, uvicorn, pydantic, httpx, pytest,
  python-dotenv) and `.env.example` listing the three env vars with
  placeholder values.
- [ ] **Step 8: Run test, verify it passes**
- [ ] **Step 9: Commit**

```bash
git add backend/requirements.txt backend/.env.example backend/app backend/tests
git commit -m "feat: backend scaffolding, settings, health check"
```

---

### Task 2: Database schema and access layer

**Files:**
- Create: `backend/app/db.py`
- Test: `backend/tests/test_db.py`

**Interfaces:**
- Consumes: `config.Settings.db_path` (Task 1).
- Produces: `db.get_connection(db_path: str) -> sqlite3.Connection` and
  `db.init_db(conn: sqlite3.Connection) -> None`, creating tables `topics`,
  `lessons`, `quizzes`, `progress`, `users` exactly as fielded in spec §6
  (use `TEXT` for JSON columns `content`/`questions`, store them as
  `json.dumps(...)`).

- [ ] **Step 1: Write failing test asserting all 5 tables exist after `init_db`**

```python
def test_init_db_creates_all_tables(tmp_path):
    conn = get_connection(str(tmp_path / "test.db"))
    init_db(conn)
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"topics", "lessons", "quizzes", "progress", "users"} <= tables
```

- [ ] **Step 2: Run test, verify it fails**
- [ ] **Step 3: Implement `db.py`** with `CREATE TABLE IF NOT EXISTS`
  statements matching spec §6 fields exactly, plus indices on
  `lessons.topic_id` and `progress.telegram_id`.
- [ ] **Step 4: Run test, verify it passes**
- [ ] **Step 5: Commit**

```bash
git add backend/app/db.py backend/tests/test_db.py
git commit -m "feat: SQLite schema and connection helper"
```

---

### Task 3: Telegram initData verification (security core)

**Files:**
- Create: `backend/app/telegram_auth.py`
- Test: `backend/tests/test_telegram_auth.py`

**Interfaces:**
- Consumes: `config.Settings.bot_token`, `config.Settings.admin_id`,
  `config.Settings.init_data_max_age_seconds` (Task 1).
- Produces:
  - `telegram_auth.verify_init_data(init_data: str, bot_token: str,
    max_age_seconds: int) -> dict | None` — returns the parsed fields
    (including a `user` dict with an `id` key) if the HMAC signature is
    valid AND `auth_date` is within `max_age_seconds` of now; otherwise
    `None`. Algorithm: Telegram's documented `data-check-string` + HMAC-SHA256
    keyed with `HMAC-SHA256("WebAppData", bot_token)`.
  - `telegram_auth.require_verified_user(x_telegram_init_data: str =
    Header(...)) -> dict` — FastAPI dependency; raises `HTTPException(403)`
    if `verify_init_data` returns `None` or the `user` field is missing;
    otherwise returns the `user` dict.
  - `telegram_auth.require_admin(user: dict =
    Depends(require_verified_user)) -> dict` — FastAPI dependency; raises
    `HTTPException(403)` if `user["id"] != settings.admin_id`; otherwise
    returns `user`.

- [ ] **Step 1: Write the 4 mandatory security tests**

```python
def test_rejects_missing_init_data(client):
    resp = client.get("/api/admin/_probe")  # no header at all
    assert resp.status_code in (401, 403)

def test_rejects_tampered_signature(client, make_init_data):
    bad = make_init_data(user_id=ADMIN_ID, tamper=True)
    resp = client.get("/api/admin/_probe", headers={"X-Telegram-Init-Data": bad})
    assert resp.status_code == 403

def test_rejects_valid_signature_wrong_user(client, make_init_data):
    data = make_init_data(user_id=ADMIN_ID + 1, tamper=False)
    resp = client.get("/api/admin/_probe", headers={"X-Telegram-Init-Data": data})
    assert resp.status_code == 403

def test_accepts_valid_signature_admin_user(client, make_init_data):
    data = make_init_data(user_id=ADMIN_ID, tamper=False)
    resp = client.get("/api/admin/_probe", headers={"X-Telegram-Init-Data": data})
    assert resp.status_code == 200
```

  Add a `make_init_data` fixture in `backend/tests/conftest.py` that builds a
  correctly formatted `initData` string signed with a test `BOT_TOKEN`
  (`tamper=True` flips one character of the hash). Add a throwaway
  `GET /api/admin/_probe` route in the test app (or reuse Task 6's real admin
  route once it exists — if testing before Task 6, add the probe route in
  this task's test app fixture only, not in production router).

- [ ] **Step 2: Run tests, verify all 4 fail**
- [ ] **Step 3: Implement `telegram_auth.py` per the Interfaces block above**
- [ ] **Step 4: Write failing test for stale `auth_date` (replay protection)**

```python
def test_rejects_stale_init_data(make_init_data):
    old = make_init_data(user_id=ADMIN_ID, auth_date_offset_seconds=-90000)
    assert verify_init_data(old, TEST_BOT_TOKEN, max_age_seconds=86400) is None
```

- [ ] **Step 5: Run test, verify it fails, then passes after implementation**
- [ ] **Step 6: Run full test file, verify all tests pass**
- [ ] **Step 7: Commit**

```bash
git add backend/app/telegram_auth.py backend/tests/test_telegram_auth.py backend/tests/conftest.py
git commit -m "feat: verified Telegram initData auth + admin dependency"
```

---

### Task 4: Public read API (topics, lessons, quizzes)

**Files:**
- Create: `backend/app/schemas.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/public.py`
- Modify: `backend/app/main.py` (include router)
- Test: `backend/tests/test_public_api.py`

**Interfaces:**
- Consumes: `db.get_connection`/`init_db` (Task 2).
- Produces: Pydantic schemas `Topic`, `Lesson`, `Quiz` (fields per spec §6,
  `content`/`questions` exposed as parsed JSON, not raw strings) in
  `schemas.py`. Router mounted at `/api`:
  - `GET /api/topics` → `list[Topic]`, published only, ordered by `order`.
  - `GET /api/topics/{topic_id}/lessons` → `list[Lesson]`, published only.
  - `GET /api/lessons/{lesson_id}` → `Lesson` or 404.
  - `GET /api/quizzes` → `list[Quiz]` where `lesson_id IS NULL`, published only.
  - `GET /api/quizzes/{quiz_id}` → `Quiz` or 404.

- [ ] **Step 1: Write failing tests for each endpoint** seeding 2 topics (one
  unpublished), 1 lesson each, 1 standalone quiz, asserting unpublished rows
  are excluded and 404s are returned for missing ids.
- [ ] **Step 2: Write failing test for malformed quiz JSON (Review Focus item)**

```python
def test_quiz_with_malformed_questions_json_is_skipped(client, seed_db):
    seed_db.execute(
        "INSERT INTO quizzes (title, questions, lesson_id, is_published) "
        "VALUES ('broken', 'not json', NULL, 1)")
    resp = client.get("/api/quizzes")
    assert resp.status_code == 200
    assert "broken" not in [q["title"] for q in resp.json()]
```

- [ ] **Step 3: Run tests, verify they fail**
- [ ] **Step 4: Implement `schemas.py` and `routers/public.py`** — on JSON
  decode failure for a row, log and exclude that row rather than raising.
- [ ] **Step 5: Run tests, verify they pass**
- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas.py backend/app/routers/public.py backend/app/main.py backend/tests/test_public_api.py
git commit -m "feat: public read-only topics/lessons/quizzes API"
```

---

### Task 5: Progress API

**Files:**
- Create: `backend/app/routers/progress.py`
- Modify: `backend/app/main.py` (include router)
- Test: `backend/tests/test_progress_api.py`

**Interfaces:**
- Consumes: `telegram_auth.require_verified_user` (Task 3), `db` (Task 2).
- Produces: `schemas.ProgressIn` (`lesson_id: int | None`, `quiz_id: int |
  None`, `quiz_score: int | None`) and `schemas.ProgressOut`. Router at
  `/api`:
  - `POST /api/progress` — requires verified user; `telegram_id` taken from
    the dependency, never from the body; upserts a progress row; returns
    `ProgressOut`.
  - `GET /api/progress/me` — requires verified user; returns all progress
    rows plus aggregate `completed_lessons`/`total_lessons` for that
    `telegram_id`.
  - `DELETE /api/users/me` — requires verified user; deletes the `users` row
    and all `progress` rows for that `telegram_id` (spec §11, backs the
    bot's `/delete_my_data` command); returns `{"deleted": true}`.

- [ ] **Step 1: Write failing test: no `initData` header → 401/403, no row written**
- [ ] **Step 2: Write failing test: valid `initData` → `POST /api/progress`
  persists a row keyed by the verified `telegram_id`, ignoring any
  `telegram_id` field present in the request body**
- [ ] **Step 3: Write failing test: `GET /api/progress/me` returns only the
  caller's own rows, never another user's**
- [ ] **Step 4: Write failing test: `DELETE /api/users/me` removes the
  caller's `users` row and all their `progress` rows, and leaves other
  users' rows untouched**
- [ ] **Step 5: Run tests, verify they fail**
- [ ] **Step 6: Implement `routers/progress.py`**
- [ ] **Step 7: Run tests, verify they pass**
- [ ] **Step 8: Commit**

```bash
git add backend/app/routers/progress.py backend/app/main.py backend/tests/test_progress_api.py
git commit -m "feat: Telegram-authenticated progress API"
```

---

### Task 6: Admin API (CRUD + the real probe route)

**Files:**
- Create: `backend/app/routers/admin.py`
- Modify: `backend/app/main.py` (include router)
- Test: `backend/tests/test_admin_api.py`

**Interfaces:**
- Consumes: `telegram_auth.require_admin` (Task 3), `schemas.Topic/Lesson/Quiz`
  (Task 4), `db` (Task 2).
- Produces: Router at `/api/admin`, every route depends on `require_admin`:
  - `POST /api/admin/topics`, `PUT /api/admin/topics/{id}`, `DELETE
    /api/admin/topics/{id}`
  - `POST /api/admin/lessons`, `PUT /api/admin/lessons/{id}`, `DELETE
    /api/admin/lessons/{id}`
  - `POST /api/admin/quizzes`, `PUT /api/admin/quizzes/{id}`, `DELETE
    /api/admin/quizzes/{id}`
  - `GET /api/admin/stats` → `{topic_id: {completed_count: int}}`

- [ ] **Step 1: Write failing tests** for each CRUD route confirming: (a) a
  request without a valid admin-signed `initData` is rejected (reuse the
  Task 3 fixtures — this proves the real production route, not just the
  Task 3 throwaway probe), and (b) with valid admin auth, create/update/
  delete work and are reflected in subsequent `GET /api/topics` (Task 4).
- [ ] **Step 2: Run tests, verify they fail**
- [ ] **Step 3: Implement `routers/admin.py`**
- [ ] **Step 4: Remove the throwaway `_probe` route from Task 3's test app**
  now that a real admin route exists to exercise the same dependency.
- [ ] **Step 5: Run tests, verify they pass**
- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/admin.py backend/app/main.py backend/tests/test_admin_api.py
git commit -m "feat: admin CRUD API protected by verified Telegram admin auth"
```

---

### Task 7: Notifications (reminders + broadcast)

**Files:**
- Create: `backend/app/notifications.py`
- Create: `backend/app/scripts/send_reminders.py`
- Modify: `backend/app/routers/admin.py` (add broadcast endpoint)
- Test: `backend/tests/test_notifications.py`

**Interfaces:**
- Consumes: `db` (Task 2), `config.Settings` (Task 1), `telegram_auth.require_admin` (Task 3).
- Produces:
  - `notifications.find_inactive_users(conn, days: int) -> list[int]` — telegram_ids
    whose `last_activity_at` is older than `days` (or who have none).
  - `notifications.send_message(bot_token: str, chat_id: int, text: str,
    sender=httpx.post) -> bool` — posts to `https://api.telegram.org/bot
    {token}/sendMessage`; `sender` is injectable for tests.
  - `notifications.send_reminders(conn, settings, sender=httpx.post) -> int`
    — returns count of messages sent.
  - `notifications.broadcast(conn, settings, text: str, only_inactive_days:
    int | None, sender=httpx.post) -> int` — returns count sent (0 if no
    matching users — Review Focus item).
  - `POST /api/admin/broadcast` (admin-only) — body `{text: str,
    only_inactive_days: int | None}`, calls `notifications.broadcast`.
  - `backend/app/scripts/send_reminders.py` — standalone script (run via
    cron) calling `notifications.send_reminders` with real settings.
  - `backend/app/scripts/bot.py` — minimal long-polling loop (`getUpdates`)
    handling two commands: `/start` (static welcome text with a link to
    open the Mini App) and `/delete_my_data` (calls the same deletion logic
    as `DELETE /api/users/me` from Task 5, keyed by the message's
    `chat_id`, and replies with a confirmation).

- [ ] **Step 1: Write failing test for `find_inactive_users`** seeding users
  with varying `last_activity_at`, asserting only those older than N days
  (or null) are returned.
- [ ] **Step 2: Write failing test for `send_reminders`** using a fake
  `sender` callable that records calls instead of hitting the network;
  assert it's called once per inactive user with that user's chat id.
- [ ] **Step 3: Write failing test: `broadcast` with `only_inactive_days` set
  and zero matching users returns `0` and calls `sender` zero times**
  (Review Focus item).
- [ ] **Step 4: Write failing test: `POST /api/admin/broadcast` without
  admin auth → 403; with admin auth → 200 and the returned count matches
  the fake sender's call count**
- [ ] **Step 5: Run tests, verify they fail**
- [ ] **Step 6: Write failing test for the `/delete_my_data` handler in
  `bot.py`**, calling it directly with a fake `chat_id`, asserting the
  user/progress rows are gone and a confirmation reply is sent (reuse the
  injectable `sender` pattern from Step 2).
- [ ] **Step 7: Run tests, verify they fail**
- [ ] **Step 8: Implement `notifications.py`, the broadcast route, and
  `scripts/send_reminders.py` and `scripts/bot.py`**
- [ ] **Step 9: Run tests, verify they pass**
- [ ] **Step 10: Commit**

```bash
git add backend/app/notifications.py backend/app/scripts/send_reminders.py backend/app/scripts/bot.py backend/app/routers/admin.py backend/tests/test_notifications.py
git commit -m "feat: reminder/broadcast notifications and bot commands"
```

---

## Frontend

### Task 8: Frontend scaffolding, Telegram environment detection, bottom nav

**Files:**
- Create: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/index.html`
- Create: `frontend/src/main.tsx`, `frontend/src/App.tsx`
- Create: `frontend/src/telegram.ts`
- Create: `frontend/src/components/BottomNav.tsx`
- Test: `frontend/src/telegram.test.ts`

**Interfaces:**
- Produces:
  - `telegram.isTelegramEnv(): boolean` — true iff `window.Telegram?.WebApp`
    exists.
  - `telegram.getInitData(): string | null` — returns
    `window.Telegram.WebApp.initData` or `null` outside Telegram.
  - `App.tsx` — React Router with 4 routes matching spec §3 tabs; `BottomNav`
    renders the 4 fixed tabs in the fixed order with "Темы" as the default
    (`/`) route.

- [ ] **Step 1: Write failing test for `isTelegramEnv`/`getInitData`**

```ts
test("returns false/null outside Telegram", () => {
  expect(isTelegramEnv()).toBe(false);
  expect(getInitData()).toBeNull();
});
test("returns true/string when Telegram WebApp is present", () => {
  (window as any).Telegram = { WebApp: { initData: "abc" } };
  expect(isTelegramEnv()).toBe(true);
  expect(getInitData()).toBe("abc");
});
```

- [ ] **Step 2: Run test (`npx vitest run`), verify it fails**
- [ ] **Step 3: Implement `telegram.ts`**
- [ ] **Step 4: Run test, verify it passes**
- [ ] **Step 5: Scaffold Vite+React+Router project** (`package.json` with
  react, react-dom, react-router-dom, vite, vitest only — no extra UI
  libraries per Global Constraints), `App.tsx` with 4 routes and
  `BottomNav.tsx` rendering the approved mockup's 4 tabs/icons in order.
- [ ] **Step 6: Commit**

```bash
git add frontend/package.json frontend/vite.config.ts frontend/index.html frontend/src/main.tsx frontend/src/App.tsx frontend/src/telegram.ts frontend/src/telegram.test.ts frontend/src/components/BottomNav.tsx
git commit -m "feat: frontend scaffolding, Telegram env detection, bottom nav"
```

---

### Task 9: Topics, lessons, lesson content + quiz pages

**Files:**
- Create: `frontend/src/api.ts`
- Create: `frontend/src/quizLogic.ts`
- Create: `frontend/src/pages/TopicsPage.tsx`, `LessonsPage.tsx`,
  `LessonContentPage.tsx`
- Test: `frontend/src/quizLogic.test.ts`

**Interfaces:**
- Consumes: `GET /api/topics`, `GET /api/topics/{id}/lessons`, `GET
  /api/lessons/{id}` (Task 4); `telegram.getInitData` (Task 8).
- Produces:
  - `api.getTopics(): Promise<Topic[]>`, `api.getTopicLessons(topicId:
    number): Promise<Lesson[]>`, `api.getLesson(id: number):
    Promise<Lesson>`, `api.submitProgress(payload): Promise<void>` (no-op
    and resolves immediately if `telegram.getInitData()` is `null`).
  - `quizLogic.scoreQuiz(questions: {correct_index: number}[], answers:
    number[]): {score: number, total: number}` — pure function.
  - Pages render per the approved mockups: `TopicsPage` (default route `/`)
    lists topic cards with progress bars; `LessonsPage` lists lessons with
    completed/current/locked-looking states; `LessonContentPage` renders
    step-by-step content then the lesson's quiz, submitting progress via
    `api.submitProgress` only when `telegram.isTelegramEnv()` is true.

- [ ] **Step 1: Write failing test for `scoreQuiz`**

```ts
test("scores correct and incorrect answers", () => {
  const questions = [{correct_index: 0}, {correct_index: 1}];
  expect(scoreQuiz(questions, [0, 1])).toEqual({score: 2, total: 2});
  expect(scoreQuiz(questions, [1, 1])).toEqual({score: 1, total: 2});
});
```

- [ ] **Step 2: Run test, verify it fails**
- [ ] **Step 3: Implement `quizLogic.ts`**
- [ ] **Step 4: Run test, verify it passes**
- [ ] **Step 5: Implement `api.ts` and the three pages** per the approved
  mockups (`.superpowers/brainstorm/.../screen-topics.html`,
  `screen-lessons.html`, `screen-lesson-content.html`).
- [ ] **Step 6: Manually verify** by running `npm run dev` and checking the
  three screens against the approved mockups in a browser.
- [ ] **Step 7: Commit**

```bash
git add frontend/src/api.ts frontend/src/quizLogic.ts frontend/src/quizLogic.test.ts frontend/src/pages/TopicsPage.tsx frontend/src/pages/LessonsPage.tsx frontend/src/pages/LessonContentPage.tsx
git commit -m "feat: topics/lessons/lesson-content pages with quiz scoring"
```

---

### Task 10: Quizzes tab, Progress tab, About tab

**Files:**
- Create: `frontend/src/pages/QuizzesPage.tsx`, `QuizPage.tsx`,
  `ProgressPage.tsx`, `AboutPage.tsx`
- Modify: `frontend/src/api.ts` (add `getQuizzes`, `getProgress`)

**Interfaces:**
- Consumes: `GET /api/quizzes`, `GET /api/progress/me` (Tasks 4, 5),
  `quizLogic.scoreQuiz` (Task 9), `telegram.isTelegramEnv` (Task 8).
- Produces: `api.getQuizzes(): Promise<Quiz[]>`, `api.getProgress():
  Promise<ProgressOut>`. `ProgressPage` shows the Task 8/5-gated "open in
  Telegram" placeholder when `!telegram.isTelegramEnv()`, otherwise renders
  per the approved mockup. `AboutPage` links to the privacy policy (Task 12)
  and includes the notifications on/off toggle (persisted via a future
  settings endpoint is out of scope — toggle may be local-only for MVP,
  matching spec §10's `notifications_enabled` field stored server-side only
  once a user record exists from a progress call).

- [ ] **Step 1: Implement the four pages** per the approved mockups
  (`screen-quizzes.html`, `screen-progress-about.html`).
- [ ] **Step 2: Manually verify** against the approved mockups in a browser,
  including the non-Telegram placeholder state on `ProgressPage`.
- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/QuizzesPage.tsx frontend/src/pages/QuizPage.tsx frontend/src/pages/ProgressPage.tsx frontend/src/pages/AboutPage.tsx frontend/src/api.ts
git commit -m "feat: quizzes, progress, and about pages"
```

---

### Task 11: Admin frontend

**Files:**
- Create: `frontend/src/admin/AdminApp.tsx`, `AdminTopics.tsx`,
  `AdminBroadcast.tsx`
- Modify: `frontend/src/App.tsx` (mount `/admin` route)

**Interfaces:**
- Consumes: `/api/admin/*` (Task 6, 7), `telegram.getInitData` (Task 8).
- Produces: `/admin` route rendering per the approved admin mockup
  (`screen-admin.html`): topics table with create/edit, and a broadcast form
  (text + optional "inactive for N days" filter). Every request attaches
  `X-Telegram-Init-Data` from `telegram.getInitData()`; a `403` response
  renders a plain "Доступ запрещён" message — the actual enforcement is
  server-side (Task 3/6), this page never attempts its own authorization
  decision.

- [ ] **Step 1: Implement the admin pages and route.**
- [ ] **Step 2: Manually verify**: opening `/admin` outside Telegram (no
  `initData`) shows "Доступ запрещён" because the backend rejects every
  call — confirms the frontend adds no false sense of security.
- [ ] **Step 3: Commit**

```bash
git add frontend/src/admin frontend/src/App.tsx
git commit -m "feat: admin frontend for topics/lessons/quizzes and broadcast"
```

---

## Deployment

### Task 12: Deployment artifacts, privacy policy template, deploy docs

**Files:**
- Create: `deploy/finedu.service`
- Create: `deploy/finedu-bot.service`
- Create: `deploy/nginx.conf.example`
- Create: `docs/privacy-policy-template.md`
- Create: `docs/deploy.md`

**Interfaces:**
- Produces: a `systemd` unit running `uvicorn app.main:app` from `backend/`
  with `EnvironmentFile=/etc/finedu/.env`; a second `systemd` unit
  (`finedu-bot.service`) running `python -m app.scripts.bot` with the same
  `EnvironmentFile`, so `/start` and `/delete_my_data` (Task 7) work
  independently of the API process; an nginx server block proxying
  `moneyedu.ru` (HTTP→HTTPS redirect + `proxy_pass` to the uvicorn port)
  with a `certbot` comment showing the exact command to obtain the
  certificate; a privacy policy template matching spec §11 (what's
  collected: only `telegram_id`; where stored: server in Russia, cloud.ru;
  how to delete: `/delete_my_data` bot command); a deploy doc covering
  first-time setup (clone, `.env` creation, DNS A-record to the cloud.ru IP,
  certbot, `systemctl enable --now finedu`) and routine content updates
  (admin panel — no redeploy needed; code changes — `git pull`, rebuild
  frontend, `systemctl restart finedu`).

- [ ] **Step 1: Write `deploy/finedu.service` and `deploy/finedu-bot.service`**
- [ ] **Step 2: Write `deploy/nginx.conf.example`**
- [ ] **Step 3: Write `docs/privacy-policy-template.md`**
- [ ] **Step 4: Write `docs/deploy.md`**
- [ ] **Step 5: Run the full backend (`pytest backend/`) and frontend
  (`npx vitest run` in `frontend/`) test suites one final time; confirm all
  pass, including the 4 mandatory security tests from Task 3.**
- [ ] **Step 6: Commit**

```bash
git add deploy docs/privacy-policy-template.md docs/deploy.md
git commit -m "docs: deployment artifacts, privacy policy template, deploy guide"
```

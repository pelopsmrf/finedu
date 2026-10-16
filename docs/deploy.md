# Finedu — установка и обновление

## Текущий сервер: xorek (Франкфурт), рядом со средой агента

Почему не cloud.ru: с российских серверов не открывается `api.telegram.org`,
без него не работают бот, напоминания и рассылки.

Как устроено:

| Что | Где |
|---|---|
| Код (клон GitHub), venv, собранный фронтенд | `/srv/finedu` (владелец `cloudcli`) |
| База SQLite | `/var/lib/finedu/finedu.db` (владелец `finedu`) |
| Секреты | `/etc/finedu/finedu.env` (root:finedu, 640) |
| API | служба `finedu`, `127.0.0.1:8010` |
| Бот | служба `finedu-bot` |
| Напоминания | `finedu-remind.timer`, каждый день в 10:00 МСК |
| HTTPS и статика | Caddy, блок `moneyedu.ru` в `/etc/caddy/Caddyfile` |

Файлы: `deploy/xorek/` (службы, блок Caddy, `setup.sh`, `update.sh`).

### Установка (один раз, нужен root)

1. **DNS** (Timeweb): A-записи `moneyedu.ru` и `www.moneyedu.ru` → `2.27.68.56`.
2. Под root:
   ```bash
   sudo bash /srv/cloudcli/projects/finedu/finedu/deploy/xorek/setup.sh
   ```
   Скрипт спросит токен бота и ваш Telegram ID, создаст ключ админки и покажет
   его один раз — сохраните. Дальше сам: пользователь `finedu`, код, сборка,
   стартовые уроки, службы, блок Caddy (с проверкой и копией прежнего файла).
   Повторный запуск безопасен.
3. **BotFather**: Mini App URL и кнопка меню → `https://moneyedu.ru`.

### Обновление кода (root не нужен)

```bash
bash /srv/finedu/deploy/xorek/update.sh
```

`git pull`, зависимости, сборка, затем перезапуск API и бота: скрипт касается
файла `/srv/finedu/.restart`, а `finedu-restart.path` (systemd) перезапускает службы.

### Полезное

- Логи: `journalctl -u finedu -u finedu-bot -n 50`
- Сменить токен/ключ: правка `/etc/finedu/finedu.env` под root, затем
  `systemctl restart finedu finedu-bot`.
- Caddy на этом сервере обслуживает и среду агента (cloudcli). Если хостинг
  перезапишет `/etc/caddy/Caddyfile`, блок moneyedu.ru нужно вернуть:
  повторить `setup.sh`.

---

## Другой вариант: отдельный сервер с nginx

На серверах в РФ бот не будет работать (см. выше).

### Первоначальная установка

1. **DNS**: в панели Timeweb (где зарегистрирован `moneyedu.ru`) создайте
   A-запись `moneyedu.ru → <IP вашего сервера на cloud.ru>`.
2. **Клонирование кода** на сервер в `/opt/finedu`.
3. **Backend**:
   ```bash
   cd /opt/finedu/backend
   python3 -m venv venv
   ./venv/bin/pip install -r requirements.txt
   ```
4. **Секреты**: скопируйте `backend/.env.example` в `/etc/finedu/.env` и
   заполните реальный `FINEDU_BOT_TOKEN` (из BotFather), `FINEDU_ADMIN_ID`
   (ваш Telegram ID), `FINEDU_DB_PATH=/var/lib/finedu/finedu.db` и
   `FINEDU_ADMIN_TOKEN` — секретный ключ для входа в админку из браузера
   (не короче 32 символов). Сгенерировать ключ:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Этот файл **никогда** не попадает в git — только на сервере.
   Ключ сохраните в менеджере паролей: он понадобится для входа в админку.
5. **Frontend**:
   ```bash
   cd /opt/finedu/frontend
   npm ci --include=dev   # --include=dev: иначе при NODE_ENV=production не поставится сборщик
   npm run build
   ```
   **Стартовый контент** (3 темы, 9 уроков, 11 квизов из `backend/content/starter.json`):
   ```bash
   cd /opt/finedu/backend
   set -a; . /etc/finedu/.env; set +a
   ./venv/bin/python -m app.scripts.seed_content
   ```
   Повторный запуск безопасен: уже существующие темы и квизы пропускаются,
   ваши правки в админке не затираются.
6. **Nginx + HTTPS**:
   ```bash
   sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/moneyedu.ru
   sudo ln -s /etc/nginx/sites-available/moneyedu.ru /etc/nginx/sites-enabled/
   sudo certbot certonly --nginx -d moneyedu.ru
   sudo nginx -t && sudo systemctl reload nginx
   ```
7. **Systemd-сервисы**:
   ```bash
   sudo cp deploy/finedu.service deploy/finedu-bot.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now finedu finedu-bot
   ```
8. **BotFather**: укажите `https://moneyedu.ru` как URL Mini App в настройках
   вашего бота (`/newapp` или `/myapps` → Edit Web App URL). Там же
   (`/mybots` → бот → Bot Settings → Menu Button) задайте кнопку меню с тем же
   адресом — она будет рядом с полем ввода сообщения.

## Обновление контента (темы, уроки, квизы)

Не требует редеплоя — всё управляется через админ-панель на
`https://moneyedu.ru/admin`. Вход — с любого компьютера по секретному ключу
`FINEDU_ADMIN_TOKEN` (или внутри Telegram с вашего аккаунта `FINEDU_ADMIN_ID`).

- Новая тема, урок или квиз создаются **черновиком** — пользователи их не видят,
  пока не поставите галочку «Опубликован(а)» и не нажмёте «Сохранить».
- Уроки неопубликованной темы тоже скрыты, даже если сами уроки опубликованы.
- Удаление темы удаляет все её уроки и их квизы (с подтверждением).
- Если ключ утёк — смените `FINEDU_ADMIN_TOKEN` в `/etc/finedu/.env` и
  выполните `sudo systemctl restart finedu`.

## Обновление кода (вариант с nginx)

```bash
cd /opt/finedu
git pull   # или аналогичная синхронизация, если используется не git
cd backend && ./venv/bin/pip install -r requirements.txt
cd ../frontend && npm ci --include=dev && npm run build
sudo systemctl restart finedu finedu-bot
```

## Напоминания пользователям

На сервере xorek это делает `finedu-remind.timer`. На другом сервере запускайте
`python -m app.scripts.send_reminders` по расписанию (cron),
например раз в сутки. Cron не читает `/etc/finedu/.env` сам — подключаем его
в команде (`crontab -e` под пользователем `finedu`):

```
0 10 * * * cd /opt/finedu/backend && set -a && . /etc/finedu/.env && set +a && ./venv/bin/python -m app.scripts.send_reminders
```

Как работают напоминания:
- приходят тем, кто не заходил `reminder_days` дней (по умолчанию 3);
- **одно напоминание на одну паузу**: если человек не вернулся, повторно бот
  не пишет, пока пользователь снова не позанимается и снова не пропадёт;
- в сообщении — название следующего непройденного урока и кнопка «Продолжить урок»;
- кто выключил «Напоминания от бота» во вкладке «О проекте», не получает ни
  напоминаний, ни рассылок.

## Локальный запуск для проверки

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env        # заполнить; FINEDU_DB_PATH=./finedu.db
.venv/bin/python -m app.scripts.seed_content
.venv/bin/uvicorn app.main:app --port 8000

cd ../frontend
npm ci --include=dev
npm run dev                 # http://localhost:5173, админка — /admin
```

Тесты: `cd backend && .venv/bin/python -m pytest` и `cd frontend && npm test`.

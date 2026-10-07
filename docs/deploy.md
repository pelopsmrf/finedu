# Finedu — установка и обновление

## Первоначальная установка (cloud.ru + moneyedu.ru)

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
   (ваш Telegram ID) и `FINEDU_DB_PATH=/var/lib/finedu/finedu.db`.
   Этот файл **никогда** не попадает в git — только на сервере.
5. **Frontend**:
   ```bash
   cd /opt/finedu/frontend
   npm install
   npm run build
   ```
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
   вашего бота (`/newapp` или `/myapps` → Edit Web App URL).

## Обновление контента (темы, уроки, квизы)

Не требует редеплоя — всё управляется через админ-панель на
`https://moneyedu.ru/admin` (доступна только вашему Telegram ID).

## Обновление кода

```bash
cd /opt/finedu
git pull   # или аналогичная синхронизация, если используется не git
cd backend && ./venv/bin/pip install -r requirements.txt
cd ../frontend && npm install && npm run build
sudo systemctl restart finedu finedu-bot
```

## Напоминания пользователям

Запускайте `python -m app.scripts.send_reminders` по расписанию (cron),
например раз в сутки:

```
0 10 * * * cd /opt/finedu/backend && ./venv/bin/python -m app.scripts.send_reminders
```

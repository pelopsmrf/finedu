#!/usr/bin/env bash
# One-time installation of finedu (moneyedu.ru) on the xorek server. Run as root:
#   sudo bash /srv/cloudcli/projects/finedu/finedu/deploy/xorek/setup.sh
# Safe to run again: existing user, folders, settings and Caddy block are kept.
set -euo pipefail

REPO=https://github.com/pelopsmrf/finedu.git
APP=/srv/finedu
DEPLOY_USER=cloudcli
DEPLOY_HOME=/var/lib/cloudcli
ENV_FILE=/etc/finedu/finedu.env
CADDYFILE=/etc/caddy/Caddyfile
HERE=$(cd "$(dirname "$0")" && pwd)

[ "$(id -u)" = 0 ] || { echo "Нужен root: sudo bash $0"; exit 1; }
umask 022

echo "== 1. Пользователь finedu и папки"
id finedu >/dev/null 2>&1 || useradd --system --home-dir /var/lib/finedu --shell /usr/sbin/nologin finedu
install -d -o finedu -g finedu -m 750 /var/lib/finedu
install -d -o "$DEPLOY_USER" -g "$DEPLOY_USER" -m 755 "$APP"

echo "== 2. Настройки $ENV_FILE"
if [ -f "$ENV_FILE" ]; then
    echo "уже есть, не трогаю"
else
    read -rsp "Токен бота из BotFather (ввод не отображается): " BOT_TOKEN; echo
    read -rp "Ваш Telegram ID (только цифры): " ADMIN_ID
    [[ "$ADMIN_ID" =~ ^[0-9]+$ ]] || { echo "Telegram ID должен состоять из цифр"; exit 1; }
    [[ "$BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]] || { echo "Токен не похож на токен бота"; exit 1; }
    ADMIN_TOKEN=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
    install -d -o root -g finedu -m 750 /etc/finedu
    install -o root -g finedu -m 640 /dev/null "$ENV_FILE"
    cat > "$ENV_FILE" <<ENV
FINEDU_BOT_TOKEN=$BOT_TOKEN
FINEDU_ADMIN_ID=$ADMIN_ID
FINEDU_DB_PATH=/var/lib/finedu/finedu.db
FINEDU_ADMIN_TOKEN=$ADMIN_TOKEN
FINEDU_WEBAPP_URL=https://moneyedu.ru
ENV
    echo
    echo "  Ключ входа в админку (https://moneyedu.ru/admin):"
    echo "  $ADMIN_TOKEN"
    echo "  Сохраните его в менеджере паролей. Он также лежит в $ENV_FILE"
    echo
fi

echo "== 3. Код, зависимости, сборка (от имени $DEPLOY_USER)"
if [ ! -d "$APP/.git" ]; then
    runuser -u "$DEPLOY_USER" -- env HOME="$DEPLOY_HOME" bash -c "umask 022; git clone -q $REPO $APP"
fi
runuser -u "$DEPLOY_USER" -- env HOME="$DEPLOY_HOME" bash "$APP/deploy/xorek/update.sh"

echo "== 4. Службы systemd"
install -m 644 "$HERE"/systemd/* /etc/systemd/system/
systemctl daemon-reload

echo "== 5. Стартовые уроки (повторный запуск ничего не затирает)"
runuser -u finedu -- bash -c "set -a; . $ENV_FILE; set +a; cd $APP/backend && $APP/venv/bin/python -m app.scripts.seed_content"

systemctl enable --now finedu.service finedu-bot.service finedu-remind.timer finedu-restart.path
systemctl restart finedu.service finedu-bot.service

echo "== 6. Caddy: блок moneyedu.ru"
if grep -q "^moneyedu.ru" "$CADDYFILE"; then
    echo "блок уже есть, не трогаю"
else
    BACKUP="$CADDYFILE.bak-$(date +%F-%H%M)"
    cp -a "$CADDYFILE" "$BACKUP"
    # Check the new config on a copy first, so a mistake never reaches the live Caddy.
    NEW=$(mktemp)
    cat "$CADDYFILE" "$HERE/Caddyfile.moneyedu" > "$NEW"
    if ! caddy validate --config "$NEW" --adapter caddyfile; then
        rm -f "$NEW"
        echo "Ошибка в настройке Caddy — файл не изменён, ничего не сломано."
        exit 1
    fi
    cat "$NEW" > "$CADDYFILE"
    rm -f "$NEW"
    systemctl reload caddy
    echo "копия прежнего файла: $BACKUP"
fi

echo "== 7. Проверка"
sleep 3
for unit in finedu finedu-bot finedu-remind.timer finedu-restart.path caddy; do
    printf '  %-22s %s\n' "$unit" "$(systemctl is-active $unit)"
done
printf '  API: '; curl -s --max-time 5 http://127.0.0.1:8010/api/health; echo
echo "Готово. Когда DNS moneyedu.ru укажет на этот сервер, Caddy сам получит HTTPS-сертификат."

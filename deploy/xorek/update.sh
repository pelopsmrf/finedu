#!/usr/bin/env bash
# Update finedu on the xorek server. Runs as the deploy user (cloudcli), no root needed:
#   bash /srv/finedu/deploy/xorek/update.sh
# Pulls the code, installs dependencies, builds the frontend and asks systemd
# (finedu-restart.path) to restart the API and the bot.
set -euo pipefail
umask 022   # cloudcli's default umask is 077: finedu and caddy could not read the files
APP=/srv/finedu
cd "$APP"

git pull --ff-only -q

if [ ! -x venv/bin/pip ]; then
    # The system Python has no ensurepip/pip, so bootstrap pip with get-pip.py.
    python3 -m venv --without-pip venv
    curl -sS --max-time 120 https://bootstrap.pypa.io/get-pip.py | venv/bin/python - -q
fi
venv/bin/pip install -q -r backend/requirements.txt

cd frontend
npm ci --include=dev --no-audit --no-fund --loglevel=error   # NODE_ENV=production would skip vite
# Build next to the live copy and swap, so the site never serves a half-built folder.
rm -rf dist.new dist.old
npx vite build --outDir dist.new --emptyOutDir --logLevel warn
[ -d dist ] && mv dist dist.old
mv dist.new dist
rm -rf dist.old

touch "$APP/.restart"
echo "finedu обновлён: $(git -C "$APP" log -1 --format='%h %s')"

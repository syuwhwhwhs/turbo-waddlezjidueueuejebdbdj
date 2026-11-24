#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="RoXeT BoT"
APP_DIR="/opt/roxet-bot"
SERVICE_USER=""

banner() {
  clear 2>/dev/null || true
  echo "===================================================="
  echo "                 RoXeT BoT"
  echo "             TELEGRAM BOT INSTALLER"
  echo "===================================================="
  echo
}

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root: sudo su - ; bash install.sh"
  exit 1
fi

banner
printf "This installer will configure %s on this server.\n\n" "$APP_NAME"

# Choose a non-root service account. The bot itself must not run as root.
if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]] && id "${SUDO_USER}" >/dev/null 2>&1; then
  SERVICE_USER="$SUDO_USER"
else
  SERVICE_USER="$(getent passwd 1000 | cut -d: -f1 || true)"
fi
if [[ -z "$SERVICE_USER" || "$SERVICE_USER" == "root" ]]; then
  read -r -p "Linux username to run the bot (non-root): " SERVICE_USER
fi
if ! id "$SERVICE_USER" >/dev/null 2>&1 || [[ "$SERVICE_USER" == "root" ]]; then
  echo "Invalid service user. Create a normal Linux user first."
  exit 1
fi

read -r -s -p "Telegram Bot Token: " BOT_TOKEN; echo
[[ -n "$BOT_TOKEN" ]] || { echo "Bot token is required."; exit 1; }
read -r -p "Bot username (without @): " BOT_USERNAME
BOT_USERNAME="${BOT_USERNAME#@}"
[[ -n "$BOT_USERNAME" ]] || { echo "Bot username is required."; exit 1; }
read -r -p "Admin Telegram ID(s), comma-separated: " ADMIN_IDS
[[ "$ADMIN_IDS" =~ ^[0-9]+(,[0-9]+)*$ ]] || { echo "Invalid admin ID(s)."; exit 1; }
read -r -p "Mini App HTTPS URL (example https://bot.example.com): " WEBAPP_URL
[[ "$WEBAPP_URL" =~ ^https://[^[:space:]]+$ ]] || { echo "A valid HTTPS URL is required for Telegram Mini Apps."; exit 1; }
read -r -p "Web server port [8000]: " PORT
PORT="${PORT:-8000}"
[[ "$PORT" =~ ^[0-9]+$ ]] && (( PORT >= 1 && PORT <= 65535 )) || { echo "Invalid port."; exit 1; }

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -f "$SOURCE_DIR/run.py" || ! -f "$SOURCE_DIR/server.py" ]]; then
  echo "Run this installer from the RoXeT BoT project directory."
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
echo
echo "[1/5] Installing system packages..."
apt-get update
apt-get install -y python3-venv python3-pip ffmpeg fonts-noto-core rsync

echo "[2/5] Preparing application directory..."
mkdir -p "$APP_DIR"
rsync -a --delete \
  --exclude='.git' --exclude='.venv' --exclude='.env' --exclude='data/' \
  "$SOURCE_DIR/" "$APP_DIR/"
mkdir -p "$APP_DIR/data/work"
chown -R "$SERVICE_USER":"$SERVICE_USER" "$APP_DIR"

echo "[3/5] Installing Python dependencies..."
sudo -u "$SERVICE_USER" python3 -m venv "$APP_DIR/.venv"
sudo -u "$SERVICE_USER" "$APP_DIR/.venv/bin/python" -m pip install --upgrade pip wheel
sudo -u "$SERVICE_USER" "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "[4/5] Saving private configuration..."
install -o "$SERVICE_USER" -g "$SERVICE_USER" -m 600 /dev/null "$APP_DIR/.env"
cat > "$APP_DIR/.env" <<EOF
BOT_TOKEN=${BOT_TOKEN}
BOT_USERNAME=${BOT_USERNAME}
WEBAPP_URL=${WEBAPP_URL}
ADMIN_IDS=${ADMIN_IDS}
DATABASE_PATH=data/studio.db
WORK_DIR=data/work
HOST=127.0.0.1
PORT=${PORT}
EOF
chown "$SERVICE_USER":"$SERVICE_USER" "$APP_DIR/.env"
chmod 600 "$APP_DIR/.env"
unset BOT_TOKEN

cat > /etc/systemd/system/roxet-bot.service <<EOF
[Unit]
Description=RoXeT BoT Telegram Worker
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/.venv/bin/python ${APP_DIR}/run.py
Restart=always
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/roxet-web.service <<EOF
[Unit]
Description=RoXeT BoT Mini App Web Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/.venv/bin/python ${APP_DIR}/server.py
Restart=always
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

echo "[5/5] Enabling services..."
systemctl daemon-reload
systemctl enable --now roxet-bot.service roxet-web.service

echo
echo "===================================================="
echo "             RoXeT BoT INSTALLED"
echo "===================================================="
echo "Bot service:    systemctl status roxet-bot"
echo "Web service:    systemctl status roxet-web"
echo "Logs:           journalctl -u roxet-bot -f"
echo "App directory:  ${APP_DIR}"
echo "Web port:       ${PORT}"
echo "Config:         ${APP_DIR}/.env (private)"
echo "===================================================="

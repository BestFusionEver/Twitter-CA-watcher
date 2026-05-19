#!/usr/bin/env bash
set -euo pipefail

APP_NAME="x-ca-watcher"
APP_USER="xwatcher"
APP_DIR="/opt/${APP_NAME}"
CONFIG_DIR="/etc/${APP_NAME}"
STATE_DIR="/var/lib/${APP_NAME}"
ENV_FILE="/etc/${APP_NAME}.env"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo bash install.sh"
  exit 1
fi

if [[ ! -f "x_ca_watcher/__main__.py" ]]; then
  echo "Run this script from the project root directory."
  exit 1
fi

echo "[1/7] Installing system packages"
apt update
apt install -y python3 python3-venv rsync

echo "[2/7] Creating service user and directories"
if ! id "${APP_USER}" >/dev/null 2>&1; then
  useradd --system --home "${APP_DIR}" --shell /usr/sbin/nologin "${APP_USER}"
fi
mkdir -p "${APP_DIR}" "${CONFIG_DIR}" "${STATE_DIR}"
chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}" "${STATE_DIR}"

echo "[3/7] Copying application files"
rsync -a \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude "__pycache__" \
  --exclude "state" \
  ./ "${APP_DIR}/"
chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

echo "[4/7] Creating Python virtualenv"
sudo -u "${APP_USER}" python3 -m venv "${APP_DIR}/.venv"
sudo -u "${APP_USER}" "${APP_DIR}/.venv/bin/python" -m pip install --upgrade pip
sudo -u "${APP_USER}" "${APP_DIR}/.venv/bin/python" -m pip install -r "${APP_DIR}/requirements.txt"

echo "[5/7] Installing config files"
if [[ ! -f "${CONFIG_DIR}/config.json" ]]; then
  cp "${APP_DIR}/deploy/config.prod.example.json" "${CONFIG_DIR}/config.json"
fi
if [[ ! -f "${ENV_FILE}" ]]; then
  cp "${APP_DIR}/deploy/x-ca-watcher.env.example" "${ENV_FILE}"
fi
chown root:"${APP_USER}" "${ENV_FILE}"
chmod 640 "${ENV_FILE}"
chown -R root:"${APP_USER}" "${CONFIG_DIR}"
chmod 770 "${CONFIG_DIR}"
chmod 660 "${CONFIG_DIR}/config.json"

echo "[6/7] Installing systemd service"
cp "${APP_DIR}/deploy/${APP_NAME}.service" "${SERVICE_FILE}"
systemctl daemon-reload
systemctl enable "${APP_NAME}"

echo "[7/7] Testing application imports"
sudo -u "${APP_USER}" "${APP_DIR}/.venv/bin/python" -m unittest discover -s "${APP_DIR}/tests"

cat <<EOF

Install complete.

Next edit these files:
  nano ${ENV_FILE}
  nano ${CONFIG_DIR}/config.json

Then start the bot:
  systemctl start ${APP_NAME}

Check logs:
  journalctl -u ${APP_NAME} -f

EOF

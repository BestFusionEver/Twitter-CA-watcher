#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f "x_ca_watcher/__main__.py" ]]; then
  echo "Run this script from the project root directory."
  exit 1
fi

echo "[1/4] Creating local Python virtualenv"
python3 -m venv .venv

echo "[2/4] Installing Python requirements"
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo "[3/4] Creating local config files"
if [[ ! -f ".env" ]]; then
  cp .env.example .env
fi
if [[ ! -f "config.json" ]]; then
  cp config.example.json config.json
fi

echo "[4/4] Running tests"
.venv/bin/python -m unittest discover -s tests

cat <<EOF

Trial environment is ready.

Now edit:
  nano .env
  nano config.json

Then test once without sending notifications:
  .venv/bin/python -m x_ca_watcher run --config config.json --dry-run

Then test live stream without sending notifications:
  .venv/bin/python -m x_ca_watcher stream --config config.json --dry-run

When it works, send real notifications:
  .venv/bin/python -m x_ca_watcher stream --config config.json

EOF


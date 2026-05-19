# VPS Deployment

This guide targets current Ubuntu LTS servers. Ubuntu 24.04 LTS is recommended.

## 1. Prepare The Server

For one-command installation, run this from the project directory:

```bash
sudo bash install.sh
```

Then edit these files:

```bash
sudo nano /etc/x-ca-watcher.env
sudo nano /etc/x-ca-watcher/config.json
sudo systemctl start x-ca-watcher
```

Manual installation steps are below.

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3 python3-venv
```

## 2. Create The App User

```bash
sudo useradd --system --home /opt/x-ca-watcher --shell /usr/sbin/nologin xwatcher
sudo mkdir -p /opt/x-ca-watcher /etc/x-ca-watcher /var/lib/x-ca-watcher
sudo chown -R xwatcher:xwatcher /opt/x-ca-watcher /var/lib/x-ca-watcher
```

## 3. Put The Code On The Server

If you use Git:

```bash
sudo git clone YOUR_REPO_URL /opt/x-ca-watcher
sudo chown -R xwatcher:xwatcher /opt/x-ca-watcher
```

Without Git, copy the files under `/opt/x-ca-watcher` with `scp` or `rsync`.

## 4. Create The Python Environment

```bash
cd /opt/x-ca-watcher
sudo -u xwatcher python3 -m venv .venv
sudo -u xwatcher .venv/bin/python -m pip install --upgrade pip
sudo -u xwatcher .venv/bin/python -m pip install -r requirements.txt
```

## 5. Prepare Config And Secrets

```bash
sudo cp /opt/x-ca-watcher/deploy/config.prod.example.json /etc/x-ca-watcher/config.json
sudo cp /opt/x-ca-watcher/deploy/x-ca-watcher.env.example /etc/x-ca-watcher.env
sudo nano /etc/x-ca-watcher/config.json
sudo nano /etc/x-ca-watcher.env
```

Set watched accounts in `/etc/x-ca-watcher/config.json`:

```json
{
  "accounts": ["account1", "account2"],
  "include_likes": false,
  "max_results_per_account": 10,
  "state_db": "/var/lib/x-ca-watcher/watcher.sqlite3"
}
```

Set X and alert secrets in `/etc/x-ca-watcher.env`:

```bash
X_BEARER_TOKEN=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

Tighten file permissions:

```bash
sudo chown root:xwatcher /etc/x-ca-watcher.env
sudo chmod 640 /etc/x-ca-watcher.env
sudo chown -R root:xwatcher /etc/x-ca-watcher
sudo chmod 770 /etc/x-ca-watcher
sudo chmod 660 /etc/x-ca-watcher/config.json
```

## 6. Install The Service

```bash
sudo cp /opt/x-ca-watcher/deploy/x-ca-watcher.service /etc/systemd/system/x-ca-watcher.service
sudo systemctl daemon-reload
sudo systemctl enable --now x-ca-watcher
```

The service runs in `stream` mode by default. It aims to alert without polling delay when selected accounts publish new posts containing detected CA values.

## 7. Check Logs

```bash
sudo systemctl status x-ca-watcher
sudo journalctl -u x-ca-watcher -f
```

## Update

```bash
cd /opt/x-ca-watcher
sudo git pull
sudo -u xwatcher .venv/bin/python -m pip install -r requirements.txt
sudo systemctl restart x-ca-watcher
```

## Suggested VPS Size

For basic use, 1 vCPU / 1 GB RAM is enough. For more watched accounts and lower intervals, 2 vCPU / 2 GB RAM or higher is more comfortable. Disk usage is low because the SQLite state file stays small.

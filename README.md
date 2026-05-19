# X CA Watcher

A lightweight watcher bot that monitors selected X accounts, detects possible token/contract addresses in posts, sends alerts, and can optionally forward detected addresses to Telegram BasedBot.

## Features

- Fetches recent posts from selected X accounts with X API v2.
- Can optionally try to inspect liked posts when your X API access allows it.
- Detects possible contract/token addresses in post text:
  - EVM: `0x...`
  - Solana/Base58-like addresses
  - Sui/Aptos-style `0x...::module::name` asset ids
- Stores seen posts in SQLite to avoid duplicate alerts.
- Sends alerts through Telegram or Discord webhook.
- Supports Telegram commands to manage watched accounts while the stream is running.
- Optional BasedBot forwarding through your own Telegram user session.

> Note: X API access depends on your plan, tier, and permissions. This bot is built around official X API endpoints; liked-post and interaction endpoints may be unavailable on some accounts or plans.

## Setup

For a local trial without installing a service:

```bash
./trial.sh
```

Then fill `.env` and `config.json`.

Manual setup:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
cp config.example.json config.json
```

At minimum, set:

```bash
X_BEARER_TOKEN=...
```

For Telegram alerts:

```bash
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

Or use Discord:

```bash
DISCORD_WEBHOOK_URL=...
```

## Usage

One-time check:

```bash
python -m x_ca_watcher run --config config.json
```

Polling mode:

```bash
python -m x_ca_watcher watch --config config.json --interval 120
```

Lowest-latency mode:

```bash
python -m x_ca_watcher stream --config config.json
```

`stream` configures X Filtered Stream rules for the selected accounts and listens while the connection is open. Some interactions, such as likes, may not arrive through stream; use `watch` polling for those cases.

Telegram account management while stream is running:

```text
/add username
/remove username
/list
```

Commands are accepted only from the `TELEGRAM_CHAT_ID` configured in `.env`.

Dry-run without sending alerts:

```bash
python -m x_ca_watcher run --config config.json --dry-run
```

Telegram/Discord alert test:

```bash
python -m x_ca_watcher notify-test --config config.json
```

Timing logs are enabled with `TIMING_LOGS=1`. Disable them with `TIMING_LOGS=0`.

Use compact alerts with `ALERT_COMPACT=1`.

## BasedBot Forwarding

Telegram bot tokens cannot message other Telegram bots. To automatically forward detected CA values to BasedBot, this project opens an MTProto session with your own Telegram user account.

`.env`:

```bash
BASEDBOT_ENABLED=1
BASEDBOT_USERNAME=based_eth_bot
BASEDBOT_SESSION=state/basedbot.session
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
```

First login:

```bash
python -m x_ca_watcher basedbot-login
```

Then run stream:

```bash
python -m x_ca_watcher stream --config config.json
```

Before enabling this, configure BasedBot Quick Buy with a small amount and the wallet/chain settings you want.

## Config

Write watched accounts by username in `config.json`:

```json
{
  "accounts": ["example", "another_example"],
  "include_likes": false,
  "max_results_per_account": 10,
  "state_db": "state/watcher.sqlite3"
}
```

When `include_likes` is `true`, the bot also tries `GET /2/users/:id/liked_tweets`. This endpoint may not be available on every X API plan.

## Test

```bash
python -m unittest discover -s tests
```

## VPS

For Ubuntu VPS deployment, use the systemd guide in [DEPLOY.md](DEPLOY.md). A small 1 vCPU / 1 GB RAM instance is enough for basic use; use 2 vCPU / 2 GB RAM or higher for more accounts and shorter polling intervals.

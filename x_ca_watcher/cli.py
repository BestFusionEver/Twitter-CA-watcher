from __future__ import annotations

import argparse
import json
import os
import threading
import time
from pathlib import Path

from .analyzer import find_addresses
from .basedbot import BasedBotSender, login_basedbot_session
from .config import Config
from .notifier import build_notifier
from .state import StateStore
from .telegram_commands import TelegramCommandListener
from .timing import log_timing
from .x_client import XClient, XClientError


def main() -> int:
    parser = argparse.ArgumentParser(prog="x-ca-watcher")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("run", "watch", "stream", "notify-test", "basedbot-login"):
        command = subparsers.add_parser(name)
        command.add_argument("--config", default="config.json")
        command.add_argument("--dry-run", action="store_true")
        if name == "watch":
            command.add_argument("--interval", type=int, default=120)

    args = parser.parse_args()
    load_dotenv(Path(".env"))
    if args.command == "basedbot-login":
        load_dotenv(Path(".env"))
        import asyncio

        asyncio.run(login_basedbot_session())
        return 0

    config_path = Path(args.config)
    config = Config.from_file(config_path)

    if args.command == "notify-test":
        build_notifier().send("X CA Watcher test bildirimi")
        print("notification test sent")
        return 0

    if args.command == "run":
        return run_once(config, dry_run=args.dry_run)

    if args.command == "stream":
        return stream(config, config_path=config_path, dry_run=args.dry_run)

    while True:
        run_once(config, dry_run=args.dry_run)
        time.sleep(max(args.interval, 15))


def run_once(config: Config, dry_run: bool = False) -> int:
    bearer = os.getenv("X_BEARER_TOKEN", "").strip()
    if not bearer:
        raise SystemExit("X_BEARER_TOKEN missing. Add it to .env or environment.")

    client = XClient(bearer)
    state = StateStore(config.state_db)
    notifier = build_notifier()
    basedbot = BasedBotSender()
    basedbot.start()

    try:
        users = client.lookup_users(config.accounts)
    except XClientError as exc:
        raise SystemExit(f"X user lookup failed: {exc}") from exc

    for username in config.accounts:
        user = users.get(username.lower())
        if user is None:
            print(f"skip @{username}: user not found")
            continue

        posts = client.user_posts(user["id"], max_results=config.max_results_per_account)
        if config.include_likes:
            posts.extend(client.liked_posts(user["id"], max_results=config.max_results_per_account))

        for post in posts:
            if state.has_seen(post.id):
                continue
            hits = find_addresses(post.text)
            state.mark_seen(post.id)
            if not hits:
                continue
            log_timing(f"CA yakalandi post_id={post.id} hit_count={len(hits)}")
            basedbot.send_hits(hits)
            message = format_alert(username=username, post=post, hits=hits)
            if dry_run:
                print(message)
            else:
                notifier.send(message)
                log_timing(f"Bildirim gonderildi post_id={post.id}")

    return 0


def stream(config: Config, config_path: Path, dry_run: bool = False) -> int:
    bearer = os.getenv("X_BEARER_TOKEN", "").strip()
    if not bearer:
        raise SystemExit("X_BEARER_TOKEN missing. Add it to .env or environment.")

    client = XClient(bearer)
    state = StateStore(config.state_db)
    notifier = build_notifier()
    basedbot = BasedBotSender()
    basedbot.start()
    account_lock = threading.Lock()

    def add_account(username: str) -> str:
        clean = username.strip().lstrip("@")
        if not clean:
            return "Kullanım: /add hesap_adi"
        with account_lock:
            if clean.lower() in {account.lower() for account in config.accounts}:
                return f"@{clean} zaten takipte."
            config.accounts.append(clean)
            config.save(config_path)
            client.sync_stream_rules(config.accounts)
        return f"@{clean} eklendi."

    def remove_account(username: str) -> str:
        clean = username.strip().lstrip("@")
        if not clean:
            return "Kullanım: /remove hesap_adi"
        with account_lock:
            before = len(config.accounts)
            config.accounts[:] = [account for account in config.accounts if account.lower() != clean.lower()]
            if len(config.accounts) == before:
                return f"@{clean} takip listesinde yok."
            config.save(config_path)
            client.sync_stream_rules(config.accounts)
        return f"@{clean} kaldırıldı."

    def list_accounts() -> str:
        with account_lock:
            if not config.accounts:
                return "Takip listesi boş."
            return "Takip edilenler:\n" + "\n".join(f"- @{account}" for account in config.accounts)

    TelegramCommandListener(
        on_add=add_account,
        on_remove=remove_account,
        on_list=list_accounts,
    ).start()

    client.sync_stream_rules(config.accounts)
    print("stream started for: " + ", ".join(f"@{account}" for account in config.accounts))

    for post in client.filtered_stream():
        if state.has_seen(post.id):
            continue
        hits = find_addresses(post.text)
        state.mark_seen(post.id)
        if not hits:
            continue
        log_timing(f"CA yakalandi post_id={post.id} hit_count={len(hits)}")
        basedbot.send_hits(hits)
        username = post.author_username or "unknown"
        message = format_alert(username=username, post=post, hits=hits)
        if dry_run:
            print(message)
        else:
            notifier.send(message)
            log_timing(f"Bildirim gonderildi post_id={post.id}")

    return 0


def format_alert(username: str, post, hits) -> str:
    if os.getenv("ALERT_COMPACT", "0").strip().lower() in {"1", "true", "yes", "on"}:
        addresses = "\n".join(hit.address for hit in hits)
        return "\n".join(
            [
                "CA",
                addresses,
                f"https://x.com/{post.author_username or username}/status/{post.id}",
            ]
        )

    lines = [
        "CA bulundu",
        f"Hesap: @{username}",
        f"Post: https://x.com/{post.author_username or username}/status/{post.id}",
        "",
        "Adresler:",
    ]
    for hit in hits:
        lines.append(f"- {hit.address} ({hit.chain_hint}, {hit.confidence})")
    lines.extend(["", "Metin:", _trim(post.text, 700)])
    return "\n".join(lines)


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _trim(text: str, limit: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1] + "…"

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass


class Notifier:
    def send(self, message: str) -> None:
        raise NotImplementedError


@dataclass
class ConsoleNotifier(Notifier):
    def send(self, message: str) -> None:
        print(message)


@dataclass
class TelegramNotifier(Notifier):
    bot_token: str
    chat_id: str

    def send(self, message: str) -> None:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        body = urllib.parse.urlencode({"chat_id": self.chat_id, "text": message}).encode()
        request = urllib.request.Request(url, data=body, method="POST")
        with urllib.request.urlopen(request, timeout=20) as response:
            response.read()


@dataclass
class DiscordNotifier(Notifier):
    webhook_url: str

    def send(self, message: str) -> None:
        body = json.dumps({"content": message[:1900]}).encode()
        request = urllib.request.Request(
            self.webhook_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            response.read()


def build_notifier() -> Notifier:
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if telegram_token and telegram_chat_id:
        return TelegramNotifier(telegram_token, telegram_chat_id)

    discord_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if discord_url:
        return DiscordNotifier(discord_url)

    return ConsoleNotifier()


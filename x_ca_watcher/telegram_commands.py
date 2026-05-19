from __future__ import annotations

import json
import os
import threading
import time
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class TelegramCommandListener:
    on_add: Callable[[str], str]
    on_remove: Callable[[str], str]
    on_list: Callable[[], str]

    def start(self) -> None:
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        if not token or not chat_id:
            return

        thread = threading.Thread(target=self._run, args=(token, chat_id), daemon=True)
        thread.start()

    def _run(self, token: str, allowed_chat_id: str) -> None:
        offset = None
        while True:
            try:
                updates = self._get_updates(token, offset)
                for update in updates:
                    offset = int(update["update_id"]) + 1
                    response = self._handle_update(update, allowed_chat_id)
                    if response:
                        self._send_message(token, allowed_chat_id, response)
            except Exception as exc:
                print(f"telegram command listener error: {exc}")
                time.sleep(5)

    def _handle_update(self, update: dict[str, Any], allowed_chat_id: str) -> str | None:
        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat") or {}
        if str(chat.get("id")) != str(allowed_chat_id):
            return None

        text = str(message.get("text") or "").strip()
        if not text.startswith("/"):
            return None

        command, _, rest = text.partition(" ")
        command = command.split("@", 1)[0].lower()
        argument = rest.strip()

        if command == "/add":
            return self.on_add(argument)
        if command in {"/remove", "/rm", "/del"}:
            return self.on_remove(argument)
        if command == "/list":
            return self.on_list()
        if command in {"/help", "/start"}:
            return (
                "Commands:\n"
                "/add username - add account to watch list\n"
                "/remove username - remove account from watch list\n"
                "/list - show watch list"
            )
        return None

    def _get_updates(self, token: str, offset: int | None) -> list[dict[str, Any]]:
        params = {"timeout": "25"}
        if offset is not None:
            params["offset"] = str(offset)
        url = f"https://api.telegram.org/bot{token}/getUpdates?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=35) as response:
            payload = json.loads(response.read())
        if not payload.get("ok"):
            raise RuntimeError(payload)
        return payload.get("result", [])

    def _send_message(self, token: str, chat_id: str, message: str) -> None:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        body = urllib.parse.urlencode({"chat_id": chat_id, "text": message}).encode()
        request = urllib.request.Request(url, data=body, method="POST")
        with urllib.request.urlopen(request, timeout=20) as response:
            response.read()

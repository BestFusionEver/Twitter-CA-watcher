from __future__ import annotations

import asyncio
import os
import threading
from pathlib import Path

from .analyzer import AddressHit
from .timing import log_timing


class BasedBotSender:
    def __init__(self) -> None:
        self.enabled = os.getenv("BASEDBOT_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
        self.username = os.getenv("BASEDBOT_USERNAME", "based_eth_bot").strip().lstrip("@")
        self.session_path = Path(os.getenv("BASEDBOT_SESSION", "state/basedbot.session"))
        self.api_id = os.getenv("TELEGRAM_API_ID", "").strip()
        self.api_hash = os.getenv("TELEGRAM_API_HASH", "").strip()
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._client = None
        self._entity = None
        self._ready = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if not self.enabled:
            return
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=15)

    def send_hits(self, hits: list[AddressHit]) -> None:
        if not self.enabled:
            return
        addresses = [hit.address for hit in hits if hit.chain_hint in {"evm", "move_asset"}]
        if not addresses:
            return
        with self._lock:
            if self._loop and self._client:
                future = asyncio.run_coroutine_threadsafe(self._send_with_client(addresses), self._loop)
                future.result(timeout=15)
            else:
                asyncio.run(self._send(addresses))

    def _run_loop(self) -> None:
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._prepare_client())
        self._ready.set()
        loop.run_forever()

    async def _prepare_client(self) -> None:
        client = await self._new_client()
        if not await client.is_user_authorized():
            await client.disconnect()
            raise RuntimeError("BasedBot Telegram session is not authorized. Run basedbot-login first.")
        self._client = client
        self._entity = await client.get_entity(self.username)

    async def _send(self, addresses: list[str]) -> None:
        client = await self._new_client()
        try:
            for address in addresses:
                await client.send_message(self.username, address)
                log_timing(f"BasedBot'a gonderildi address={address}")
        finally:
            await client.disconnect()

    async def _send_with_client(self, addresses: list[str]) -> None:
        for address in addresses:
            await self._client.send_message(self._entity or self.username, address)
            log_timing(f"BasedBot'a gonderildi address={address}")

    async def _new_client(self):
        if not self.api_id or not self.api_hash:
            raise RuntimeError("TELEGRAM_API_ID and TELEGRAM_API_HASH are required for BasedBot sending")
        try:
            from telethon import TelegramClient
        except ImportError as exc:
            raise RuntimeError("Telethon is not installed. Run: .venv/bin/python -m pip install -r requirements.txt") from exc

        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        client = TelegramClient(str(self.session_path), int(self.api_id), self.api_hash)
        await client.connect()
        return client


async def login_basedbot_session() -> None:
    api_id = os.getenv("TELEGRAM_API_ID", "").strip()
    api_hash = os.getenv("TELEGRAM_API_HASH", "").strip()
    session_path = Path(os.getenv("BASEDBOT_SESSION", "state/basedbot.session"))
    if not api_id or not api_hash:
        raise SystemExit("TELEGRAM_API_ID and TELEGRAM_API_HASH are required in .env")

    try:
        from telethon import TelegramClient
    except ImportError as exc:
        raise SystemExit("Telethon is not installed. Run: .venv/bin/python -m pip install -r requirements.txt") from exc

    session_path.parent.mkdir(parents=True, exist_ok=True)
    client = TelegramClient(str(session_path), int(api_id), api_hash)
    await client.start()
    await client.disconnect()
    print(f"BasedBot Telegram session saved: {session_path}")

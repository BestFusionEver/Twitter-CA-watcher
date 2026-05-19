from __future__ import annotations

import os
from datetime import datetime, timezone


def timing_enabled() -> bool:
    return os.getenv("TIMING_LOGS", "1").strip().lower() not in {"0", "false", "no", "off"}


def log_timing(message: str) -> None:
    if not timing_enabled():
        return
    timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")
    print(f"[{timestamp}] {message}", flush=True)


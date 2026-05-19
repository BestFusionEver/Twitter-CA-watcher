from __future__ import annotations

import sqlite3
from pathlib import Path


class StateStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def has_seen(self, post_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute("select 1 from seen_posts where post_id = ?", (post_id,)).fetchone()
        return row is not None

    def mark_seen(self, post_id: str) -> None:
        with self._connect() as conn:
            conn.execute("insert or ignore into seen_posts(post_id) values (?)", (post_id,))

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                create table if not exists seen_posts (
                    post_id text primary key,
                    seen_at datetime default current_timestamp
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)


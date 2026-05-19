from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    accounts: list[str]
    include_likes: bool
    max_results_per_account: int
    state_db: Path

    @classmethod
    def from_file(cls, path: Path) -> "Config":
        data = json.loads(path.read_text(encoding="utf-8"))
        accounts = data.get("accounts", [])
        if not isinstance(accounts, list) or not all(isinstance(item, str) for item in accounts):
            raise ValueError("config.accounts must be a list of usernames")
        clean_accounts = [item.strip().lstrip("@") for item in accounts if item.strip()]
        if not clean_accounts:
            raise ValueError("config.accounts must contain at least one username")
        return cls(
            accounts=clean_accounts,
            include_likes=bool(data.get("include_likes", False)),
            max_results_per_account=int(data.get("max_results_per_account", 10)),
            state_db=Path(data.get("state_db", "state/watcher.sqlite3")),
        )

    def save(self, path: Path) -> None:
        data = {
            "accounts": self.accounts,
            "include_likes": self.include_likes,
            "max_results_per_account": self.max_results_per_account,
            "state_db": str(self.state_db),
        }
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

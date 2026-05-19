from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


API_BASE = "https://api.x.com/2"


class XClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class Post:
    id: str
    text: str
    author_id: str | None = None
    author_username: str | None = None


class XClient:
    def __init__(self, bearer_token: str) -> None:
        self.bearer_token = bearer_token

    def lookup_users(self, usernames: list[str]) -> dict[str, dict[str, str]]:
        params = {"usernames": ",".join(usernames), "user.fields": "id,username,name"}
        data = self._get("/users/by", params)
        result: dict[str, dict[str, str]] = {}
        for user in data.get("data", []):
            result[user["username"].lower()] = user
        return result

    def user_posts(self, user_id: str, max_results: int = 10) -> list[Post]:
        params = {
            "max_results": str(_clamp(max_results, 5, 100)),
            "tweet.fields": "author_id,created_at,referenced_tweets,public_metrics",
            "expansions": "author_id",
            "user.fields": "username",
            "exclude": "retweets",
        }
        data = self._get(f"/users/{user_id}/tweets", params)
        return _posts_from_payload(data)

    def liked_posts(self, user_id: str, max_results: int = 10) -> list[Post]:
        params = {
            "max_results": str(_clamp(max_results, 5, 100)),
            "tweet.fields": "author_id,created_at,referenced_tweets,public_metrics",
            "expansions": "author_id",
            "user.fields": "username",
        }
        try:
            data = self._get(f"/users/{user_id}/liked_tweets", params)
        except XClientError as exc:
            print(f"likes skipped for user_id={user_id}: {exc}")
            return []
        return _posts_from_payload(data)

    def sync_stream_rules(self, usernames: list[str]) -> None:
        wanted = {
            f"x-ca-watcher:{username.lower()}": f"from:{username.lstrip('@')} -is:retweet"
            for username in usernames
        }
        existing = self._get("/tweets/search/stream/rules", {})
        existing_rules = existing.get("data", [])
        delete_ids = [
            rule["id"]
            for rule in existing_rules
            if str(rule.get("tag", "")).startswith("x-ca-watcher:")
            and wanted.get(rule.get("tag", "")) != rule.get("value")
        ]
        existing_by_tag = {rule.get("tag"): rule.get("value") for rule in existing_rules}

        if delete_ids:
            self._request_json(
                "/tweets/search/stream/rules",
                method="POST",
                body={"delete": {"ids": delete_ids}},
            )

        additions = [
            {"value": value, "tag": tag}
            for tag, value in wanted.items()
            if existing_by_tag.get(tag) != value
        ]
        if additions:
            self._request_json(
                "/tweets/search/stream/rules",
                method="POST",
                body={"add": additions},
            )

    def filtered_stream(self):
        params = {
            "tweet.fields": "author_id,created_at,public_metrics,referenced_tweets",
            "expansions": "author_id",
            "user.fields": "username",
        }
        query = urllib.parse.urlencode(params)
        request = urllib.request.Request(
            f"{API_BASE}/tweets/search/stream?{query}",
            headers={"Authorization": f"Bearer {self.bearer_token}"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                for raw_line in response:
                    line = raw_line.strip()
                    if not line:
                        continue
                    payload = json.loads(line)
                    posts = _posts_from_payload({"data": [payload["data"]], "includes": payload.get("includes", {})})
                    if posts:
                        yield posts[0]
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise XClientError(f"stream HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise XClientError(f"stream failed: {exc.reason}") from exc

    def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        query = urllib.parse.urlencode(params)
        request = urllib.request.Request(
            f"{API_BASE}{path}?{query}",
            headers={"Authorization": f"Bearer {self.bearer_token}"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise XClientError(f"HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise XClientError(str(exc.reason)) from exc

        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise XClientError("invalid JSON response from X API") from exc

    def _request_json(self, path: str, method: str, body: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(body).encode()
        request = urllib.request.Request(
            f"{API_BASE}{path}",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json",
            },
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise XClientError(f"HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise XClientError(str(exc.reason)) from exc
        if not raw:
            return {}
        return json.loads(raw)


def _posts_from_payload(payload: dict[str, Any]) -> list[Post]:
    users = {
        user["id"]: user.get("username")
        for user in payload.get("includes", {}).get("users", [])
        if "id" in user
    }
    posts: list[Post] = []
    for item in payload.get("data", []):
        author_id = item.get("author_id")
        posts.append(
            Post(
                id=item["id"],
                text=item.get("text", ""),
                author_id=author_id,
                author_username=users.get(author_id),
            )
        )
    return posts


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))

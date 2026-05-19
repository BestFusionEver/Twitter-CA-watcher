from __future__ import annotations

import re
from dataclasses import dataclass


EVM_ADDRESS_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
MOVE_ASSET_RE = re.compile(
    r"\b0x[a-fA-F0-9]{1,64}::[A-Za-z_][A-Za-z0-9_]*::[A-Za-z_][A-Za-z0-9_]*\b"
)
BASE58_RE = re.compile(r"(?<![A-Za-z0-9])[1-9A-HJ-NP-Za-km-z]{32,44}(?![A-Za-z0-9])")

FALSE_POSITIVE_WORDS = {
    "11111111111111111111111111111111",
}


@dataclass(frozen=True)
class AddressHit:
    chain_hint: str
    address: str
    confidence: str


def find_addresses(text: str) -> list[AddressHit]:
    hits: list[AddressHit] = []
    seen: set[str] = set()

    for match in MOVE_ASSET_RE.finditer(text):
        value = match.group(0)
        _append_unique(hits, seen, AddressHit("move_asset", value, "high"))

    for match in EVM_ADDRESS_RE.finditer(text):
        value = match.group(0)
        _append_unique(hits, seen, AddressHit("evm", value, "high"))

    for match in BASE58_RE.finditer(text):
        value = match.group(0)
        if value in FALSE_POSITIVE_WORDS:
            continue
        if _looks_like_plain_word(value):
            continue
        _append_unique(hits, seen, AddressHit("solana_or_base58", value, "medium"))

    return hits


def _append_unique(hits: list[AddressHit], seen: set[str], hit: AddressHit) -> None:
    key = hit.address.lower()
    if key in seen:
        return
    seen.add(key)
    hits.append(hit)


def _looks_like_plain_word(value: str) -> bool:
    has_digit = any(char.isdigit() for char in value)
    has_mixed_case = any(char.islower() for char in value) and any(char.isupper() for char in value)
    return not has_digit and not has_mixed_case


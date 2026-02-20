"""In-memory cooldown tracker for care and talk actions.

Timestamps are not persisted — cooldowns reset on daemon restart.
"""
from __future__ import annotations

import time

CARE_COOLDOWN_SECONDS = 120.0
TALK_COOLDOWN_SECONDS = 10.0

_last_care_at: float = 0.0
_last_talk_at: float = 0.0


def check_care_cooldown() -> float | None:
    """Return seconds remaining if on cooldown, else ``None``."""
    remaining = CARE_COOLDOWN_SECONDS - (time.time() - _last_care_at)
    return remaining if remaining > 0 else None


def record_care() -> None:
    global _last_care_at
    _last_care_at = time.time()


def check_talk_cooldown() -> float | None:
    """Return seconds remaining if on cooldown, else ``None``."""
    remaining = TALK_COOLDOWN_SECONDS - (time.time() - _last_talk_at)
    return remaining if remaining > 0 else None


def record_talk() -> None:
    global _last_talk_at
    _last_talk_at = time.time()

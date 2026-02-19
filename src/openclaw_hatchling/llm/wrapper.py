"""Single LLM wrapper — all LLM calls go through here.

Handles direct provider and OpenClaw gateway modes, per-call token cap,
daily budget enforcement, and graceful degradation.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

import httpx

from openclaw_hatchling.daemon.config import HatchlingConfig

logger = logging.getLogger(__name__)


class LLMWrapper:
    def __init__(self, config: HatchlingConfig) -> None:
        self._config = config
        self._tokens_used_today: int = 0
        self._budget_date: date = date.today()
        self._client = httpx.AsyncClient(timeout=30.0)
        self._budget_exhausted_callback: Any = None

    def set_budget_exhausted_callback(self, callback: Any) -> None:
        self._budget_exhausted_callback = callback

    @property
    def tokens_used_today(self) -> int:
        self._maybe_reset_budget()
        return self._tokens_used_today

    @property
    def budget_remaining(self) -> int:
        self._maybe_reset_budget()
        return max(0, self._config.max_tokens_per_day - self._tokens_used_today)

    @property
    def budget_exhausted(self) -> bool:
        return self.budget_remaining < self._config.max_tokens_per_call

    def _maybe_reset_budget(self) -> bool:
        """Reset daily budget if the date has changed. Returns True if reset."""
        today = date.today()
        if today != self._budget_date:
            self._tokens_used_today = 0
            self._budget_date = today
            return True
        return False

    async def call(
        self, messages: list[dict[str, str]], max_tokens: int | None = None
    ) -> str | None:
        """Make an LLM completion call. Returns None if budget exhausted or error."""
        was_reset = self._maybe_reset_budget()

        cap = min(
            max_tokens or self._config.max_tokens_per_call,
            self._config.max_tokens_per_call,
        )

        if self._tokens_used_today + cap > self._config.max_tokens_per_day:
            if self._budget_exhausted_callback and not was_reset:
                await self._budget_exhausted_callback()
            return None

        try:
            url, headers, body = self._build_request(messages, cap)
            resp = await self._client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            logger.exception("LLM call failed")
            return None

        usage = data.get("usage", {})
        tokens = usage.get("total_tokens", cap)
        self._tokens_used_today += tokens

        if self._config.dev_mode:
            logger.info(
                "[dev] LLM tokens: %d this call, %d/%d today",
                tokens, self._tokens_used_today, self._config.max_tokens_per_day,
            )

        choices = data.get("choices", [])
        if not choices:
            return None
        return choices[0].get("message", {}).get("content", "")

    def _build_request(
        self, messages: list[dict[str, str]], max_tokens: int
    ) -> tuple[str, dict[str, str], dict[str, Any]]:
        cfg = self._config

        if cfg.use_openclaw_gateway:
            url = f"{cfg.openclaw_gateway_url.rstrip('/')}/v1/chat/completions"
            headers: dict[str, str] = {}
            if cfg.openclaw_gateway_token:
                headers["Authorization"] = f"Bearer {cfg.openclaw_gateway_token}"
            body: dict[str, Any] = {
                "messages": messages,
                "max_tokens": max_tokens,
            }
            if cfg.openclaw_gateway_model:
                body["model"] = cfg.openclaw_gateway_model
        else:
            url = f"{cfg.llm_base_url.rstrip('/')}/chat/completions"
            headers = {}
            if cfg.llm_api_key:
                headers["Authorization"] = f"Bearer {cfg.llm_api_key}"
            body = {
                "model": cfg.llm_model,
                "messages": messages,
                "max_tokens": max_tokens,
            }

        headers["Content-Type"] = "application/json"
        return url, headers, body

    async def health_check(self) -> bool:
        """Lightweight check for gateway reachability. Non-blocking."""
        if not self._config.use_openclaw_gateway:
            return True
        try:
            resp = await self._client.get(
                self._config.openclaw_gateway_url, timeout=5.0
            )
            return resp.status_code < 500
        except Exception:
            logger.warning(
                "OpenClaw gateway unreachable at %s",
                self._config.openclaw_gateway_url,
            )
            return False

    async def close(self) -> None:
        await self._client.aclose()

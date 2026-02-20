from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from drakeling.crypto.token import TOKEN_FILENAME
from drakeling.storage.paths import get_data_dir


class DaemonNotAvailable(Exception):
    """Raised when the daemon cannot be reached."""


class DrakelingClient:
    """Thin HTTP client for the Hatchling daemon API."""

    def __init__(self, *, base_url: str | None = None, data_dir: Path | None = None):
        self._data_dir = data_dir or get_data_dir()

        import os
        port = int(os.environ.get("HATCHLING_PORT", "52780"))
        self._base_url = base_url or f"http://127.0.0.1:{port}"
        self._client: httpx.AsyncClient | None = None

        token_path = self._data_dir / TOKEN_FILENAME
        if token_path.exists():
            self._token: str | None = token_path.read_text().strip()
        else:
            self._token = None

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            if self._token is None:
                raise DaemonNotAvailable(
                    "The Hatchling daemon has not been started yet.\n"
                    "Start it first:  drakelingd"
                )
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=5.0,
            )
        return self._client

    @property
    def has_token(self) -> bool:
        return self._token is not None

    async def ping(self) -> bool:
        """Return True if the daemon is reachable."""
        try:
            client = self._ensure_client()
            resp = await client.get("/status")
            return resp.status_code in (200, 404)
        except Exception:
            return False

    def reload_token(self) -> bool:
        """Re-read the token from disk. Returns True if found."""
        token_path = self._data_dir / TOKEN_FILENAME
        if token_path.exists():
            self._token = token_path.read_text().strip()
            self._client = None  # force re-creation with new token
            return True
        return False

    async def get_status(self) -> dict[str, Any] | None:
        """Get creature status. Returns None if no creature exists (404)."""
        client = self._ensure_client()
        resp = await client.get("/status")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    async def birth(self, colour: str, name: str) -> dict[str, Any]:
        client = self._ensure_client()
        resp = await client.post("/birth", json={"colour": colour, "name": name})
        resp.raise_for_status()
        return resp.json()

    async def care(self, care_type: str) -> dict[str, Any]:
        client = self._ensure_client()
        resp = await client.post("/care", json={"type": care_type})
        resp.raise_for_status()
        return resp.json()

    async def talk(self, message: str) -> dict[str, Any]:
        client = self._ensure_client()
        resp = await client.post("/talk", json={"message": message})
        resp.raise_for_status()
        return resp.json()

    async def rest(self) -> dict[str, Any]:
        client = self._ensure_client()
        resp = await client.post("/rest", json={})
        resp.raise_for_status()
        return resp.json()

    async def needs_attention(self) -> dict[str, Any]:
        client = self._ensure_client()
        resp = await client.get("/needs-attention")
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

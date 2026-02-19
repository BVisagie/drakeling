from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from openclaw_hatchling.crypto.token import TOKEN_FILENAME
from openclaw_hatchling.storage.paths import get_data_dir


class HatchlingClient:
    """Thin HTTP client for the Hatchling daemon API."""

    def __init__(self, *, base_url: str | None = None, data_dir: Path | None = None):
        self._data_dir = data_dir or get_data_dir()
        token_path = self._data_dir / TOKEN_FILENAME
        if not token_path.exists():
            raise FileNotFoundError(
                f"API token not found at {token_path}. "
                "Start the daemon first: openclaw-hatchlingd"
            )
        self._token = token_path.read_text().strip()

        import os
        port = int(os.environ.get("HATCHLING_PORT", "52780"))
        self._base_url = base_url or f"http://127.0.0.1:{port}"
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=10.0,
        )

    async def get_status(self) -> dict[str, Any] | None:
        """Get creature status. Returns None if no creature exists (404)."""
        resp = await self._client.get("/status")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    async def birth(self, colour: str, name: str) -> dict[str, Any]:
        resp = await self._client.post("/birth", json={"colour": colour, "name": name})
        resp.raise_for_status()
        return resp.json()

    async def care(self, care_type: str) -> dict[str, Any]:
        resp = await self._client.post("/care", json={"type": care_type})
        resp.raise_for_status()
        return resp.json()

    async def talk(self, message: str) -> dict[str, Any]:
        resp = await self._client.post("/talk", json={"message": message})
        resp.raise_for_status()
        return resp.json()

    async def rest(self) -> dict[str, Any]:
        resp = await self._client.post("/rest", json={})
        resp.raise_for_status()
        return resp.json()

    async def needs_attention(self) -> dict[str, Any]:
        resp = await self._client.get("/needs-attention")
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        await self._client.aclose()

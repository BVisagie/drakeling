from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def load_dotenv_from_data_dir(data_dir: Path) -> None:
    """Load .env from the platform data directory if it exists."""
    env_path = data_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)


def _env_bool(key: str, default: bool = False) -> bool:
    val = os.environ.get(key, "").lower()
    if val in ("true", "1", "yes"):
        return True
    if val in ("false", "0", "no", ""):
        return default
    return default


@dataclass(frozen=True)
class HatchlingConfig:
    # LLM direct provider
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    # OpenClaw gateway delegation
    use_openclaw_gateway: bool = False
    openclaw_gateway_url: str = "http://127.0.0.1:18789"
    openclaw_gateway_token: str = ""
    openclaw_gateway_model: str = ""

    # Token budget
    max_tokens_per_call: int = 300
    max_tokens_per_day: int = 10_000

    # Background loop
    tick_seconds: int = 60
    min_reflection_interval: int = 600

    # Network
    port: int = 52780

    # Runtime flags (set programmatically, not from env)
    dev_mode: bool = field(default=False, repr=False)
    allow_import: bool = field(default=False, repr=False)

    @classmethod
    def from_env(
        cls, *, dev_mode: bool = False, allow_import: bool = False
    ) -> HatchlingConfig:
        use_gw = _env_bool("HATCHLING_USE_OPENCLAW_GATEWAY")
        tick = max(10, int(os.environ.get("HATCHLING_TICK_SECONDS", "60")))
        return cls(
            llm_base_url=os.environ.get("HATCHLING_LLM_BASE_URL", ""),
            llm_api_key=os.environ.get("HATCHLING_LLM_API_KEY", ""),
            llm_model=os.environ.get("HATCHLING_LLM_MODEL", ""),
            use_openclaw_gateway=use_gw,
            openclaw_gateway_url=os.environ.get(
                "HATCHLING_OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789"
            ),
            openclaw_gateway_token=os.environ.get(
                "HATCHLING_OPENCLAW_GATEWAY_TOKEN", ""
            ),
            openclaw_gateway_model=os.environ.get(
                "HATCHLING_OPENCLAW_GATEWAY_MODEL", ""
            ),
            max_tokens_per_call=int(
                os.environ.get("HATCHLING_MAX_TOKENS_PER_CALL", "300")
            ),
            max_tokens_per_day=int(
                os.environ.get("HATCHLING_MAX_TOKENS_PER_DAY", "10000")
            ),
            tick_seconds=tick,
            min_reflection_interval=int(
                os.environ.get("HATCHLING_MIN_REFLECTION_INTERVAL", "600")
            ),
            port=int(os.environ.get("HATCHLING_PORT", "52780")),
            dev_mode=dev_mode,
            allow_import=allow_import,
        )

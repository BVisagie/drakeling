from __future__ import annotations

import os
import sys
from pathlib import Path

from drakeling.daemon.config import DrakelingConfig

ENV_TEMPLATE = """\
# Drakeling LLM Configuration
#
# Your creature needs an LLM provider to talk and reflect.
# Uncomment ONE of the options below and fill in your details.

# --- Option A: Any OpenAI-compatible LLM provider ---
# DRAKELING_LLM_BASE_URL=https://api.openai.com/v1
# DRAKELING_LLM_API_KEY=sk-...
# DRAKELING_LLM_MODEL=gpt-4o-mini

# --- Option B: OpenClaw gateway ---
# DRAKELING_USE_OPENCLAW_GATEWAY=true
# DRAKELING_OPENCLAW_GATEWAY_URL=    # leave blank for default http://127.0.0.1:18789
# DRAKELING_OPENCLAW_GATEWAY_TOKEN=  # leave blank if gateway has no auth
"""

_LLM_ENV_PREFIXES = (
    "DRAKELING_LLM_",
    "DRAKELING_USE_OPENCLAW_",
    "DRAKELING_OPENCLAW_",
)


def _llm_is_configured(config: DrakelingConfig) -> bool:
    return bool(config.llm_base_url) or config.use_openclaw_gateway


def _prompt_required(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("  This field is required.")


def _prompt_optional(prompt: str, default: str = "") -> str:
    value = input(prompt).strip()
    return value or default


def _run_wizard(env_path: Path) -> None:
    print(
        "No LLM provider configured. Let's set one up.\n"
        "\n"
        "  [1] LLM provider (any OpenAI-compatible endpoint)\n"
        "  [2] OpenClaw gateway\n"
    )

    choice = ""
    while choice not in ("1", "2"):
        choice = input("Enter 1 or 2: ").strip()

    lines: list[str] = []

    if choice == "1":
        print()
        base_url = _prompt_required("Base URL (e.g. https://api.openai.com/v1): ")
        model = _prompt_required("Model name (e.g. gpt-4o-mini): ")
        api_key = _prompt_optional("API key (leave blank for local LLMs like Ollama): ")

        lines.append(f"DRAKELING_LLM_BASE_URL={base_url}")
        lines.append(f"DRAKELING_LLM_MODEL={model}")
        if api_key:
            lines.append(f"DRAKELING_LLM_API_KEY={api_key}")

    else:
        print()
        gateway_url = _prompt_optional(
            "Gateway URL (leave blank for default http://127.0.0.1:18789): ",
            default="http://127.0.0.1:18789",
        )
        gateway_token = _prompt_optional(
            "Gateway token (leave blank if not required): ",
        )

        lines.append("DRAKELING_USE_OPENCLAW_GATEWAY=true")
        lines.append(f"DRAKELING_OPENCLAW_GATEWAY_URL={gateway_url}")
        if gateway_token:
            lines.append(f"DRAKELING_OPENCLAW_GATEWAY_TOKEN={gateway_token}")

    _write_env(env_path, lines)

    print(
        f"\nConfiguration saved to {env_path}\n"
        "Run drakelingd again to start."
    )


def _write_env(env_path: Path, new_lines: list[str]) -> None:
    """Write LLM config lines to the .env file.

    Preserves any non-LLM lines already in the file.
    """
    existing = ""
    if env_path.exists():
        existing = env_path.read_text()

    kept = [
        line for line in existing.splitlines()
        if not any(line.lstrip("# ").startswith(p) for p in _LLM_ENV_PREFIXES)
    ]

    kept = [line for line in kept if line.strip()]

    final = "\n".join(kept + new_lines) + "\n"
    env_path.write_text(final)
    if os.name != "nt":
        env_path.chmod(0o600)


def _non_tty_fallback(env_path: Path) -> None:
    if not env_path.exists():
        env_path.write_text(ENV_TEMPLATE)
        if os.name != "nt":
            env_path.chmod(0o600)
        print(
            "No LLM provider configured.\n"
            "\n"
            "A template configuration file has been created at:\n"
            f"  {env_path}\n"
            "\n"
            "Edit this file to set up your LLM provider, then run drakelingd again."
        )
    else:
        print(
            "No LLM provider configured.\n"
            "\n"
            "Edit your configuration file to set up an LLM provider:\n"
            f"  {env_path}\n"
            "\n"
            "Then run drakelingd again."
        )


def check_llm_setup(config: DrakelingConfig, data_dir: Path) -> None:
    """Check that an LLM provider is configured.

    If not and stdin is a TTY, run an interactive setup wizard.
    Otherwise fall back to creating a template .env and printing
    instructions.  Skipped in dev mode.
    """
    if config.dev_mode:
        return

    if _llm_is_configured(config):
        return

    env_path = data_dir / ".env"

    if sys.stdin.isatty():
        try:
            _run_wizard(env_path)
        except (KeyboardInterrupt, EOFError):
            print("\nSetup cancelled.")
    else:
        _non_tty_fallback(env_path)

    sys.exit(1)

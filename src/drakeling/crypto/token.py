from __future__ import annotations

import os
import secrets
from pathlib import Path

TOKEN_FILENAME = "api_token"


def generate_api_token() -> str:
    """Generate a random URL-safe API token."""
    return secrets.token_urlsafe(32)


def ensure_api_token(data_dir: Path) -> str:
    """Return the API token, generating and persisting it if it doesn't exist."""
    path = data_dir / TOKEN_FILENAME
    if path.exists():
        return path.read_text().strip()
    token = generate_api_token()
    path.write_text(token)
    if os.name != "nt":
        path.chmod(0o600)
    return token

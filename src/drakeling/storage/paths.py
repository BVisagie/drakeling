from __future__ import annotations

from pathlib import Path

import platformdirs


def get_data_dir() -> Path:
    """Return the platform-specific data directory, creating it if needed."""
    path = Path(platformdirs.user_data_dir("drakeling", "drakeling"))
    path.mkdir(parents=True, exist_ok=True)
    return path

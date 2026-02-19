from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from openclaw_hatchling.crypto.identity import verify_binding
from openclaw_hatchling.storage.models import CreatureStateRow


async def check_machine_binding(data_dir: Path, session: AsyncSession) -> None:
    """Verify that the local identity key matches the creature's public key.

    Prints a clear error and exits if the check fails.
    Called at daemon startup when a creature already exists.
    """
    result = await session.execute(select(CreatureStateRow).limit(1))
    creature = result.scalar_one_or_none()
    if creature is None:
        return  # No creature yet — nothing to check

    try:
        if not verify_binding(data_dir, creature.public_key_hex):
            print(
                "ERROR: Machine binding check failed.\n"
                "The identity key on this machine does not match the creature's "
                "stored public key.\n"
                "This creature was born on a different machine. Use export/import "
                "to relocate it.",
                file=sys.stderr,
            )
            sys.exit(1)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

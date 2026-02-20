from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from drakeling.api.app import get_session, verify_token
from drakeling.crypto.identity import PRIVATE_KEY_FILENAME
from drakeling.storage.models import (
    CreatureMemoryRow,
    CreatureStateRow,
    InteractionLogRow,
    LifecycleEventRow,
)

router = APIRouter(dependencies=[Depends(verify_token)])


class ReleaseRequest(BaseModel):
    confirm: bool = False


@router.delete("/creature")
async def release_creature(
    body: ReleaseRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    if not body.confirm:
        raise HTTPException(
            status_code=422,
            detail="Set confirm=true to release the creature.",
        )

    result = await session.execute(select(CreatureStateRow).limit(1))
    creature = result.scalar_one_or_none()
    if creature is None:
        raise HTTPException(status_code=404, detail="No creature exists")

    name = creature.name

    await session.execute(delete(CreatureMemoryRow))
    await session.execute(delete(InteractionLogRow))
    await session.execute(delete(LifecycleEventRow))
    await session.execute(delete(CreatureStateRow))
    await session.commit()

    data_dir: Path = request.app.state.data_dir
    key_path = data_dir / PRIVATE_KEY_FILENAME
    if key_path.exists():
        key_path.unlink()

    if request.app.state.config.dev_mode:
        print(f"[dev] Released creature: {name}")

    return {"status": "released", "name": name}

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from drakeling.api.app import get_session, verify_token
from drakeling.crypto.bundle import export_bundle, import_bundle
from drakeling.crypto.identity import (
    PRIVATE_KEY_FILENAME,
    save_private_key,
    verify_binding,
)
from drakeling.storage.database import DB_FILENAME
from drakeling.storage.models import CreatureStateRow, LifecycleEventRow

router = APIRouter(dependencies=[Depends(verify_token)])


class ExportRequest(BaseModel):
    passphrase: str


class ImportRequest(BaseModel):
    path: str
    passphrase: str
    force: bool = False


@router.post("/export")
async def do_export(
    body: ExportRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    data_dir: Path = request.app.state.data_dir

    result = await session.execute(select(CreatureStateRow).limit(1))
    creature = result.scalar_one_or_none()
    if creature is None:
        raise HTTPException(status_code=404, detail="No creature to export")

    bundle_bytes = export_bundle(data_dir, body.passphrase)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{creature.name}_{timestamp}.drakeling"
    out_path = data_dir / filename
    out_path.write_bytes(bundle_bytes)

    return {"path": str(out_path), "size_bytes": len(bundle_bytes)}


@router.post("/import")
async def do_import(
    body: ImportRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    config = request.app.state.config
    data_dir: Path = request.app.state.data_dir

    if not config.allow_import:
        raise HTTPException(
            status_code=403,
            detail="Import is disabled. Start the daemon with --allow-import.",
        )

    # Check for existing creature
    result = await session.execute(select(CreatureStateRow).limit(1))
    existing = result.scalar_one_or_none()
    if existing is not None and not body.force:
        raise HTTPException(
            status_code=409,
            detail="A creature already exists. Pass force=true to overwrite.",
        )

    # Read bundle
    bundle_path = Path(body.path)
    if not bundle_path.exists():
        raise HTTPException(status_code=404, detail=f"Bundle not found: {body.path}")

    try:
        bundle_bytes = bundle_path.read_bytes()
        db_bytes, key_bytes = import_bundle(bundle_bytes, body.passphrase)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    db_path = data_dir / DB_FILENAME
    key_path = data_dir / PRIVATE_KEY_FILENAME
    bak_path = None

    # Backup existing DB if force overwrite
    if existing is not None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        bak_path = data_dir / f"hatchling_{timestamp}.bak"
        shutil.copy2(db_path, bak_path)

    # Install imported data
    try:
        save_private_key(data_dir, key_bytes)
        db_path.write_bytes(db_bytes)

        # Verify binding with the imported data
        # We need to read the public key from the imported DB
        from drakeling.storage.database import get_engine, get_session_factory
        temp_engine = get_engine(data_dir)
        temp_sf = get_session_factory(temp_engine)
        async with temp_sf() as temp_session:
            res = await temp_session.execute(select(CreatureStateRow).limit(1))
            imported_creature = res.scalar_one_or_none()
            if imported_creature is None:
                raise ValueError("Imported database contains no creature")

            if not verify_binding(data_dir, imported_creature.public_key_hex):
                raise ValueError("Machine binding check failed after import")

            # Write relocated lifecycle event
            now = time.time()
            temp_session.add(LifecycleEventRow(
                created_at=now,
                event_type="relocated",
                from_stage=None,
                to_stage=imported_creature.lifecycle_stage,
                notes="Imported from bundle",
            ))
            await temp_session.commit()

        await temp_engine.dispose()

    except Exception as exc:
        # Rollback: remove imported key, restore backup
        if key_path.exists():
            key_path.unlink()
        if bak_path and bak_path.exists():
            shutil.copy2(bak_path, db_path)
        raise HTTPException(
            status_code=422,
            detail=f"Import failed, rolled back: {exc}",
        )

    return {"status": "imported", "name": imported_creature.name}

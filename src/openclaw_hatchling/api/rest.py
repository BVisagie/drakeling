from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from openclaw_hatchling.api.app import get_session, verify_token
from openclaw_hatchling.daemon.tick import _row_to_creature
from openclaw_hatchling.domain.models import LifecycleStage
from openclaw_hatchling.llm.prompts import build_rest_prompt
from openclaw_hatchling.storage.models import CreatureStateRow, LifecycleEventRow

router = APIRouter(dependencies=[Depends(verify_token)])

_RESTABLE_STAGES = {
    LifecycleStage.HATCHED.value,
    LifecycleStage.JUVENILE.value,
    LifecycleStage.MATURE.value,
}


@router.post("/rest")
async def rest(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(CreatureStateRow).limit(1))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="No creature exists")

    if row.lifecycle_stage not in _RESTABLE_STAGES:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot rest from {row.lifecycle_stage} stage",
        )

    now = time.time()
    prev_stage = row.lifecycle_stage
    row.pre_resting_stage = prev_stage
    row.lifecycle_stage = LifecycleStage.RESTING.value
    row.updated_at = now

    session.add(LifecycleEventRow(
        created_at=now,
        event_type="entered_resting",
        from_stage=prev_stage,
        to_stage=LifecycleStage.RESTING.value,
        notes="User requested rest",
    ))

    # Optional farewell expression
    llm = request.app.state.llm
    response_text = None
    if llm and not llm.budget_exhausted:
        creature = _row_to_creature(row)
        messages = build_rest_prompt(creature)
        response_text = await llm.call(messages)

    await session.commit()

    return {
        "response": response_text,
        "stage": LifecycleStage.RESTING.value,
    }

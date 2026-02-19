from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from openclaw_hatchling.api.app import get_session, verify_token
from openclaw_hatchling.domain.lifecycle import EGG_TO_HATCHED_TIME
from openclaw_hatchling.domain.models import LifecycleStage
from openclaw_hatchling.storage.models import CreatureStateRow

router = APIRouter(dependencies=[Depends(verify_token)])


@router.get("/needs-attention")
async def needs_attention(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(CreatureStateRow).limit(1))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="No creature exists")

    # Priority order: lonely -> low_mood -> low_energy -> hatching_soon
    reason = None
    urgency = None

    if row.loneliness >= 0.7:
        reason = "lonely"
        urgency = "high" if row.loneliness >= 0.9 else "medium"
    elif row.mood <= 0.2:
        reason = "low_mood"
        urgency = "high" if row.mood <= 0.1 else "medium"
    elif row.energy <= 0.2:
        reason = "low_energy"
        urgency = "medium" if row.energy <= 0.1 else "low"
    elif row.lifecycle_stage == LifecycleStage.EGG.value:
        import time
        elapsed = time.time() - row.born_at
        remaining = EGG_TO_HATCHED_TIME - elapsed
        # "Within one tick" is configurable, approximate with 60s
        if remaining <= 60 and row.cumulative_care_events >= 1:
            reason = "hatching_soon"
            urgency = "low"

    return {
        "needs_attention": reason is not None,
        "reason": reason,
        "urgency": urgency,
    }

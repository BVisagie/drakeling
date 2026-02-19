from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from openclaw_hatchling.api.app import get_session, verify_token
from openclaw_hatchling.storage.models import CreatureStateRow

router = APIRouter(dependencies=[Depends(verify_token)])


@router.get("/status")
async def status(request: Request, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(CreatureStateRow).limit(1))
    creature = result.scalar_one_or_none()
    if creature is None:
        raise HTTPException(status_code=404, detail="No creature exists")

    llm = getattr(request.app.state, "llm", None)
    budget_remaining = llm.budget_remaining if llm else None

    return {
        "name": creature.name,
        "colour": creature.colour,
        "lifecycle_stage": creature.lifecycle_stage,
        "mood": creature.mood,
        "energy": creature.energy,
        "trust": creature.trust,
        "loneliness": creature.loneliness,
        "state_curiosity": creature.state_curiosity,
        "stability": creature.stability,
        "budget_exhausted": creature.lifecycle_stage == "exhausted",
        "budget_remaining_today": budget_remaining,
    }

from __future__ import annotations

import time
from enum import StrEnum

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from drakeling.api.app import get_session, verify_token
from drakeling.domain.decay import apply_care_boost
from drakeling.domain.models import LifecycleStage, MoodState, PersonalityProfile
from drakeling.llm.prompts import build_care_prompt
from drakeling.storage.models import CreatureStateRow, InteractionLogRow

router = APIRouter(dependencies=[Depends(verify_token)])


class CareType(StrEnum):
    GENTLE_ATTENTION = "gentle_attention"
    REASSURANCE = "reassurance"
    QUIET_PRESENCE = "quiet_presence"


class CareRequest(BaseModel):
    type: str

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        try:
            CareType(v)
        except ValueError:
            raise ValueError(
                f"Invalid care type: {v}. Must be one of: "
                + ", ".join(ct.value for ct in CareType)
            )
        return v


@router.post("/care")
async def care(
    body: CareRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(CreatureStateRow).limit(1))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="No creature exists")

    now = time.time()

    # Apply stat boost
    mood = MoodState(
        mood=row.mood, energy=row.energy, trust=row.trust,
        trust_floor=row.trust_floor, loneliness=row.loneliness,
        state_curiosity=row.state_curiosity, stability=row.stability,
    )
    new_mood = apply_care_boost(mood)
    row.mood = new_mood.mood
    row.energy = new_mood.energy
    row.trust = new_mood.trust
    row.loneliness = new_mood.loneliness
    row.state_curiosity = new_mood.state_curiosity
    row.stability = new_mood.stability
    row.cumulative_care_events += 1
    row.updated_at = now

    # Try LLM response
    llm = request.app.state.llm
    response_text = None
    if llm and not llm.budget_exhausted:
        from drakeling.domain.models import Creature, DragonColour
        from drakeling.daemon.tick import _row_to_creature

        creature = _row_to_creature(row)
        messages = build_care_prompt(creature, body.type)
        response_text = await llm.call(messages)

        if response_text:
            session.add(InteractionLogRow(
                created_at=now,
                source="creature",
                interaction_type="care_response",
                content=response_text,
                care_type=body.type,
            ))

    await session.commit()

    return {
        "response": response_text,
        "state": {
            "mood": row.mood, "energy": row.energy, "trust": row.trust,
            "loneliness": row.loneliness, "state_curiosity": row.state_curiosity,
            "stability": row.stability,
        },
    }

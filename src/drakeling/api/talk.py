from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from drakeling.api.app import get_session, verify_token
from drakeling.daemon.tick import _row_to_creature
from drakeling.domain.decay import apply_talk_boost
from drakeling.domain.models import LifecycleStage, MoodState
from drakeling.llm.prompts import build_talk_prompt
from drakeling.storage.models import CreatureStateRow, InteractionLogRow

router = APIRouter(dependencies=[Depends(verify_token)])


class TalkRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if len(v) > 500:
            raise ValueError("Message must be at most 500 characters")
        if not v.strip():
            raise ValueError("Message must not be empty")
        return v


@router.post("/talk")
async def talk(
    body: TalkRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(CreatureStateRow).limit(1))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="No creature exists")

    if row.lifecycle_stage == LifecycleStage.EGG.value:
        raise HTTPException(
            status_code=403,
            detail="The creature has not yet hatched",
        )

    now = time.time()
    llm = request.app.state.llm

    # Apply talk stat boost
    creature = _row_to_creature(row)
    new_mood = apply_talk_boost(creature.mood_state, creature.personality)
    row.mood = new_mood.mood
    row.energy = new_mood.energy
    row.trust = new_mood.trust
    row.trust_floor = new_mood.trust_floor
    row.loneliness = new_mood.loneliness
    row.state_curiosity = new_mood.state_curiosity
    row.stability = new_mood.stability
    row.cumulative_talk_interactions += 1
    row.updated_at = now

    # Log user message
    session.add(InteractionLogRow(
        created_at=now,
        source="user",
        interaction_type="talk",
        content=body.message,
    ))

    # Get recent history for context
    history_result = await session.execute(
        select(InteractionLogRow)
        .where(InteractionLogRow.interaction_type == "talk")
        .order_by(desc(InteractionLogRow.created_at))
        .limit(10)
    )
    history_rows = list(reversed(history_result.scalars().all()))
    recent_history: list[dict[str, str]] = []
    for h in history_rows[-10:]:
        role = "user" if h.source == "user" else "assistant"
        recent_history.append({"role": role, "content": h.content})

    # LLM call
    if llm and not llm.budget_exhausted:
        creature = _row_to_creature(row)
        messages = build_talk_prompt(creature, body.message, recent_history)
        response_text = await llm.call(messages)

        if response_text:
            session.add(InteractionLogRow(
                created_at=now,
                source="creature",
                interaction_type="talk",
                content=response_text,
            ))
            await session.commit()
            return {
                "response": response_text,
                "state": {
                    "mood": row.mood, "energy": row.energy, "trust": row.trust,
                    "loneliness": row.loneliness,
                    "state_curiosity": row.state_curiosity,
                    "stability": row.stability,
                },
            }

    await session.commit()
    return {"response": None, "budget_exhausted": True}

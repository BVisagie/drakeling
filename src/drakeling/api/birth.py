from __future__ import annotations

import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from drakeling.api.app import get_session, verify_token
from drakeling.crypto.identity import generate_keypair, save_private_key
from drakeling.domain.models import CreatureName, DragonColour, LifecycleStage
from drakeling.domain.traits import generate_traits
from drakeling.storage.models import CreatureStateRow, LifecycleEventRow

router = APIRouter(dependencies=[Depends(verify_token)])


class BirthRequest(BaseModel):
    colour: str
    name: str

    @field_validator("colour")
    @classmethod
    def validate_colour(cls, v: str) -> str:
        try:
            DragonColour(v.lower())
        except ValueError:
            raise ValueError(
                f"Invalid colour: {v}. Must be one of: "
                + ", ".join(c.value for c in DragonColour)
            )
        return v.lower()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        CreatureName(v)
        return v.strip()


@router.post("/birth")
async def birth(
    body: BirthRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    # Reject if creature already exists
    existing = await session.execute(select(CreatureStateRow).limit(1))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="A creature already exists")

    data_dir = request.app.state.data_dir
    colour = DragonColour(body.colour)
    now = time.time()

    # Generate identity keypair FIRST — abort if this fails
    private_bytes, public_bytes = generate_keypair()
    save_private_key(data_dir, private_bytes)

    # Generate personality
    seed_hex = secrets.token_bytes(32).hex()
    personality = generate_traits(colour, seed_hex)

    # Create creature state row
    creature = CreatureStateRow(
        id=1,
        name=body.name,
        colour=colour.value,
        personality_seed=seed_hex,
        trait_curiosity=personality.trait_curiosity,
        trait_sociability=personality.trait_sociability,
        trait_confidence=personality.trait_confidence,
        trait_emotional_sensitivity=personality.trait_emotional_sensitivity,
        trait_autonomy_preference=personality.trait_autonomy_preference,
        trait_loneliness_rate=personality.trait_loneliness_rate,
        mood=0.5,
        energy=0.5,
        trust=0.5,
        trust_floor=0.0,
        loneliness=0.0,
        state_curiosity=0.5,
        stability=0.5,
        lifecycle_stage=LifecycleStage.EGG.value,
        pre_exhausted_stage=None,
        pre_resting_stage=None,
        born_at=now,
        hatched_at=None,
        public_key_hex=public_bytes.hex(),
        cumulative_care_events=0,
        cumulative_talk_interactions=0,
        last_reflection_at=None,
        updated_at=now,
    )
    session.add(creature)

    # Write born lifecycle event
    event = LifecycleEventRow(
        created_at=now,
        event_type="born",
        from_stage=None,
        to_stage=LifecycleStage.EGG.value,
        notes=f"A {colour.value} Hatchling named {body.name}",
    )
    session.add(event)
    await session.commit()

    if request.app.state.config.dev_mode:
        print(f"[dev] Birth: {body.name} ({colour.value})")

    return {
        "name": body.name,
        "colour": colour.value,
        "lifecycle_stage": LifecycleStage.EGG.value,
    }

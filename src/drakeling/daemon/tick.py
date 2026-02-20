"""Background tick loop per Spec Section 13."""
from __future__ import annotations

import asyncio
import logging
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from drakeling.daemon.config import DrakelingConfig
from drakeling.domain.decay import apply_tick_decay
from drakeling.domain.lifecycle import evaluate_transitions
from drakeling.domain.models import (
    Creature,
    LifecycleStage,
    MoodState,
    PersonalityProfile,
)
from drakeling.llm.prompts import build_reflection_prompt
from drakeling.llm.wrapper import LLMWrapper
from drakeling.storage.models import (
    CreatureMemoryRow,
    CreatureStateRow,
    LifecycleEventRow,
)

logger = logging.getLogger(__name__)


def _row_to_creature(row: CreatureStateRow) -> Creature:
    return Creature(
        name=row.name,
        colour=row.colour,
        personality=PersonalityProfile(
            seed=row.personality_seed,
            trait_curiosity=row.trait_curiosity,
            trait_sociability=row.trait_sociability,
            trait_confidence=row.trait_confidence,
            trait_emotional_sensitivity=row.trait_emotional_sensitivity,
            trait_autonomy_preference=row.trait_autonomy_preference,
            trait_loneliness_rate=row.trait_loneliness_rate,
        ),
        mood_state=MoodState(
            mood=row.mood,
            energy=row.energy,
            trust=row.trust,
            trust_floor=row.trust_floor,
            loneliness=row.loneliness,
            state_curiosity=row.state_curiosity,
            stability=row.stability,
        ),
        lifecycle_stage=LifecycleStage(row.lifecycle_stage),
        pre_exhausted_stage=(
            LifecycleStage(row.pre_exhausted_stage)
            if row.pre_exhausted_stage
            else None
        ),
        pre_resting_stage=(
            LifecycleStage(row.pre_resting_stage)
            if row.pre_resting_stage
            else None
        ),
        born_at=row.born_at,
        hatched_at=row.hatched_at,
        public_key_hex=row.public_key_hex,
        cumulative_care_events=row.cumulative_care_events,
        cumulative_talk_interactions=row.cumulative_talk_interactions,
        last_reflection_at=row.last_reflection_at,
    )


def _apply_mood_to_row(row: CreatureStateRow, ms: MoodState) -> None:
    row.mood = ms.mood
    row.energy = ms.energy
    row.trust = ms.trust
    row.trust_floor = ms.trust_floor
    row.loneliness = ms.loneliness
    row.state_curiosity = ms.state_curiosity
    row.stability = ms.stability


async def _get_resting_entered_at(session: AsyncSession) -> float | None:
    """Find the timestamp of the most recent entered_resting event."""
    from sqlalchemy import desc
    result = await session.execute(
        select(LifecycleEventRow.created_at)
        .where(LifecycleEventRow.event_type == "entered_resting")
        .order_by(desc(LifecycleEventRow.created_at))
        .limit(1)
    )
    val = result.scalar_one_or_none()
    return val


async def _do_tick(
    session_factory: async_sessionmaker[AsyncSession],
    config: DrakelingConfig,
    llm: LLMWrapper,
) -> None:
    now = time.time()

    async with session_factory() as session:
        result = await session.execute(select(CreatureStateRow).limit(1))
        row = result.scalar_one_or_none()
        if row is None:
            return

        creature = _row_to_creature(row)
        stage = creature.lifecycle_stage

        # Check for budget reset (midnight) -> restore from exhausted
        if stage == LifecycleStage.EXHAUSTED and not llm.budget_exhausted:
            prev_stage = creature.pre_exhausted_stage
            if prev_stage:
                row.lifecycle_stage = prev_stage.value
                row.pre_exhausted_stage = None
                session.add(LifecycleEventRow(
                    created_at=now,
                    event_type="budget_restored",
                    from_stage=LifecycleStage.EXHAUSTED.value,
                    to_stage=prev_stage.value,
                ))
                creature.lifecycle_stage = prev_stage
                stage = prev_stage
                if config.dev_mode:
                    logger.info("[dev] Budget restored — exiting exhausted stage")

        # Skip decay for egg stage (creature hasn't hatched yet)
        if stage != LifecycleStage.EGG:
            new_mood = apply_tick_decay(
                creature.mood_state, stage, creature.personality
            )
            _apply_mood_to_row(row, new_mood)
            creature.mood_state = new_mood

        # Evaluate lifecycle transitions
        resting_at = await _get_resting_entered_at(session) if stage == LifecycleStage.RESTING else None
        event = evaluate_transitions(creature, now, resting_entered_at=resting_at)

        if event is not None:
            row.lifecycle_stage = event.to_stage.value if event.to_stage else row.lifecycle_stage

            if event.event_type == "egg_to_hatched":
                row.hatched_at = now

            if event.event_type == "entered_resting":
                row.pre_resting_stage = event.from_stage.value if event.from_stage else None

            if event.event_type == "exited_resting":
                row.pre_resting_stage = None

            session.add(LifecycleEventRow(
                created_at=now,
                event_type=event.event_type,
                from_stage=event.from_stage.value if event.from_stage else None,
                to_stage=event.to_stage.value if event.to_stage else None,
                notes=event.notes,
            ))

            if config.dev_mode:
                logger.info("[dev] Lifecycle: %s", event.event_type)

        # Background reflection
        if not config.dev_mode and _should_reflect(creature, config, llm, now):
            messages = build_reflection_prompt(creature)
            response = await llm.call(messages)
            if response:
                session.add(CreatureMemoryRow(
                    created_at=now,
                    memory_type="reflection",
                    content=response,
                    lifecycle_stage=row.lifecycle_stage,
                ))
                row.last_reflection_at = now

        row.updated_at = now
        await session.commit()


def _should_reflect(
    creature: Creature,
    config: DrakelingConfig,
    llm: LLMWrapper,
    now: float,
) -> bool:
    stage = creature.lifecycle_stage
    if stage in (LifecycleStage.EXHAUSTED, LifecycleStage.EGG):
        return False
    if stage == LifecycleStage.RESTING and creature.mood_state.loneliness <= 0.8:
        return False
    last = creature.last_reflection_at or 0.0
    if now - last < config.min_reflection_interval:
        return False
    if llm.budget_remaining < config.max_tokens_per_call:
        return False
    return True


async def start_tick_loop(
    session_factory: async_sessionmaker[AsyncSession],
    config: DrakelingConfig,
    llm: LLMWrapper,
) -> None:
    """Run the background tick loop forever."""
    while True:
        try:
            await _do_tick(session_factory, config, llm)
        except Exception:
            logger.exception("Tick loop error")
        await asyncio.sleep(config.tick_seconds)

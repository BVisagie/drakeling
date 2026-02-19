"""Lifecycle transition evaluation per Spec Section 8.1.

Pure function: takes creature state and current time, returns an event or None.
"""
from __future__ import annotations

import time as _time

from openclaw_hatchling.domain.models import Creature, CreatureEvent, LifecycleStage

# Thresholds (seconds)
EGG_TO_HATCHED_TIME = 300          # 5 minutes
HATCHED_TO_JUVENILE_TIME = 3_600   # 1 hour
JUVENILE_TO_MATURE_TIME = 86_400   # 24 hours

EGG_TO_HATCHED_CARE = 1
HATCHED_TO_JUVENILE_CARE = 3
JUVENILE_TO_MATURE_CARE = 10
JUVENILE_TO_MATURE_TALK = 5

ENERGY_RESTING_THRESHOLD = 0.15
ENERGY_WAKE_THRESHOLD = 0.5
RESTING_MAX_DURATION = 3_600       # 1 hour


def evaluate_transitions(
    creature: Creature,
    now: float | None = None,
    *,
    resting_entered_at: float | None = None,
) -> CreatureEvent | None:
    """Check whether a lifecycle transition should occur.

    Returns a CreatureEvent if a transition fires, None otherwise.
    Only one transition per call (highest priority first).
    """
    if now is None:
        now = _time.time()

    stage = creature.lifecycle_stage

    # egg -> hatched
    if stage == LifecycleStage.EGG:
        elapsed = now - creature.born_at
        if (
            elapsed >= EGG_TO_HATCHED_TIME
            and creature.cumulative_care_events >= EGG_TO_HATCHED_CARE
        ):
            return CreatureEvent(
                event_type="egg_to_hatched",
                from_stage=LifecycleStage.EGG,
                to_stage=LifecycleStage.HATCHED,
                created_at=now,
            )
        return None

    # hatched -> juvenile
    if stage == LifecycleStage.HATCHED:
        if creature.hatched_at is not None:
            elapsed = now - creature.hatched_at
            if (
                elapsed >= HATCHED_TO_JUVENILE_TIME
                and creature.cumulative_care_events >= HATCHED_TO_JUVENILE_CARE
            ):
                return CreatureEvent(
                    event_type="hatched_to_juvenile",
                    from_stage=LifecycleStage.HATCHED,
                    to_stage=LifecycleStage.JUVENILE,
                    created_at=now,
                )
        return None

    # juvenile -> mature
    if stage == LifecycleStage.JUVENILE:
        if creature.hatched_at is not None:
            elapsed = now - creature.hatched_at
            if (
                elapsed >= JUVENILE_TO_MATURE_TIME
                and creature.cumulative_care_events >= JUVENILE_TO_MATURE_CARE
                and creature.cumulative_talk_interactions >= JUVENILE_TO_MATURE_TALK
            ):
                return CreatureEvent(
                    event_type="juvenile_to_mature",
                    from_stage=LifecycleStage.JUVENILE,
                    to_stage=LifecycleStage.MATURE,
                    created_at=now,
                )
        return None

    # mature -> resting (auto, on low energy)
    if stage == LifecycleStage.MATURE:
        if creature.mood_state.energy < ENERGY_RESTING_THRESHOLD:
            return CreatureEvent(
                event_type="entered_resting",
                from_stage=LifecycleStage.MATURE,
                to_stage=LifecycleStage.RESTING,
                created_at=now,
                notes="Energy fell below threshold",
            )
        return None

    # resting -> pre_resting_stage (wake)
    if stage == LifecycleStage.RESTING:
        wake = False
        if creature.mood_state.energy >= ENERGY_WAKE_THRESHOLD:
            wake = True
        elif resting_entered_at is not None:
            if now - resting_entered_at >= RESTING_MAX_DURATION:
                wake = True
        if wake and creature.pre_resting_stage is not None:
            return CreatureEvent(
                event_type="exited_resting",
                from_stage=LifecycleStage.RESTING,
                to_stage=creature.pre_resting_stage,
                created_at=now,
            )

    return None

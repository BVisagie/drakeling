"""Pure stat decay and boost functions per Spec Section 13.1.

All functions operate on MoodState and return a new MoodState.
No I/O, no side effects.
"""
from __future__ import annotations

from dataclasses import replace

from drakeling.domain.models import (
    LifecycleStage,
    MoodState,
    PersonalityProfile,
)


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def apply_tick_decay(
    state: MoodState,
    stage: LifecycleStage,
    traits: PersonalityProfile,
) -> MoodState:
    """Apply one tick's worth of stat decay/growth."""
    is_resting = stage == LifecycleStage.RESTING

    mood = _clamp(state.mood - 0.005)
    energy = _clamp(state.energy + (0.006 if is_resting else -0.003))

    trust = _clamp(state.trust - 0.001)
    trust_floor = state.trust_floor
    if trust < trust_floor:
        trust = trust_floor

    loneliness_delta = 0.008 * (0.5 + traits.trait_loneliness_rate)
    loneliness = _clamp(state.loneliness + loneliness_delta)

    state_curiosity = _clamp(state.state_curiosity - 0.004)
    stability = _clamp(state.stability + (0.01 if is_resting else -0.002))

    return replace(
        state,
        mood=mood,
        energy=energy,
        trust=trust,
        trust_floor=trust_floor,
        loneliness=loneliness,
        state_curiosity=state_curiosity,
        stability=stability,
    )


def apply_care_boost(state: MoodState) -> MoodState:
    """Apply stat effects of a care event."""
    return replace(
        state,
        mood=_clamp(state.mood + 0.05),
        loneliness=0.0,
    )


def apply_talk_boost(state: MoodState, traits: PersonalityProfile) -> MoodState:
    """Apply stat effects of a talk interaction."""
    trust = _clamp(state.trust + 0.02)
    trust_floor = state.trust_floor
    if trust > 0.8:
        trust_floor = _clamp(trust_floor + 0.01)

    curiosity_delta = 0.03 * (1.0 + traits.trait_curiosity)
    state_curiosity = _clamp(state.state_curiosity + curiosity_delta)

    return replace(
        state,
        mood=_clamp(state.mood + 0.05),
        trust=trust,
        trust_floor=trust_floor,
        loneliness=0.0,
        state_curiosity=state_curiosity,
    )

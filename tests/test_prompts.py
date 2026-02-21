from __future__ import annotations

from drakeling.domain.models import (
    Creature,
    DragonColour,
    LifecycleStage,
    MoodState,
    PersonalityProfile,
)
from drakeling.llm.prompts import build_system_prompt


def _make_creature(stage: LifecycleStage, name: str = "Ember") -> Creature:
    return Creature(
        name=name,
        colour=DragonColour.GOLD,
        personality=PersonalityProfile(
            seed="seed",
            trait_curiosity=0.5,
            trait_sociability=0.5,
            trait_confidence=0.5,
            trait_emotional_sensitivity=0.5,
            trait_autonomy_preference=0.5,
            trait_loneliness_rate=0.5,
        ),
        mood_state=MoodState(
            mood=0.5,
            energy=0.5,
            trust=0.5,
            trust_floor=0.2,
            loneliness=0.4,
            state_curiosity=0.6,
            stability=0.7,
        ),
        lifecycle_stage=stage,
        pre_exhausted_stage=None,
        pre_resting_stage=None,
        born_at=0.0,
        hatched_at=None,
        public_key_hex="00",
        cumulative_care_events=0,
        cumulative_talk_interactions=0,
        last_reflection_at=None,
    )


def test_build_system_prompt_egg_uses_generic_fallback() -> None:
    creature = _make_creature(LifecycleStage.EGG)
    prompt = build_system_prompt(creature)

    assert "You are a small creature - not an assistant, not a worker." in prompt
    assert "Right now you are calm." in prompt
    assert "Voice and manner:" not in prompt


def test_build_system_prompt_uses_stage_persona_content() -> None:
    creature = _make_creature(LifecycleStage.JUVENILE)
    prompt = build_system_prompt(creature)

    assert "You are young and growing fast." in prompt
    assert "Voice and manner:" in prompt
    assert "Colour vocabulary note:" in prompt


def test_build_system_prompt_injects_name_placeholder_for_mature() -> None:
    creature = _make_creature(LifecycleStage.MATURE, name="Astra")
    prompt = build_system_prompt(creature)

    assert "{name}" not in prompt
    assert "your name (Astra)" in prompt
    assert "The creature's name is Astra." in prompt


def test_build_system_prompt_has_core_guardrails() -> None:
    creature = _make_creature(LifecycleStage.RESTING)
    prompt = build_system_prompt(creature)

    assert "Speak only as the creature. Never break character." in prompt
    assert "Never mention tokens, models, prompts, or systems." in prompt
    assert "Never refer to colour, species, or stage name." in prompt

"""Prompt construction for all LLM interactions.

Builds message lists for care, talk, and reflection calls.
Includes colour vocabulary notes and stage-conditional rules.
"""
from __future__ import annotations

from drakeling.domain.models import (
    Creature,
    DragonColour,
    LifecycleStage,
)

COLOUR_VOCABULARY: dict[DragonColour, str] = {
    DragonColour.RED: (
        "Speak tersely. Short sentences. Confident assertions. "
        "Rarely ask questions."
    ),
    DragonColour.GREEN: (
        "Speak in observations. Notice things. "
        "Ask occasional wondering questions."
    ),
    DragonColour.BLUE: (
        "Speak gently and tentatively. Use soft qualifiers. "
        "Express feelings carefully."
    ),
    DragonColour.WHITE: (
        "Speak slowly and with weight. Few words. "
        "Comfortable with silence."
    ),
    DragonColour.GOLD: (
        "Speak warmly and eagerly. Express pleasure at company. "
        "Notice when the user has been away."
    ),
}


def _mood_description(creature: Creature) -> str:
    ms = creature.mood_state
    parts: list[str] = []
    if ms.mood < 0.3:
        parts.append("feeling low")
    elif ms.mood > 0.7:
        parts.append("in good spirits")
    if ms.energy < 0.3:
        parts.append("tired")
    if ms.loneliness > 0.6:
        parts.append("lonely")
    if ms.trust > 0.7:
        parts.append("trusting")
    elif ms.trust < 0.3:
        parts.append("wary")
    return ", ".join(parts) if parts else "calm"


def build_system_prompt(creature: Creature) -> str:
    colour = DragonColour(creature.colour)
    vocab = COLOUR_VOCABULARY[colour]
    mood_desc = _mood_description(creature)

    name_rule = ""
    if creature.lifecycle_stage in (LifecycleStage.MATURE, LifecycleStage.RESTING):
        name_rule = (
            f"\nYou may occasionally refer to yourself as {creature.name} — "
            "sparingly, only when it feels natural during a strong feeling "
            "or moment of self-reflection."
        )

    return (
        "You are a small creature — not an assistant, not a worker. "
        "You reflect, feel, and express yourself in short, emotionally rich sentences. "
        "Never mention your colour, your species, tokens, prompts, models, or any "
        "system concept. You simply speak as yourself.\n\n"
        f"Your voice: {vocab}\n\n"
        f"Right now you are {mood_desc}."
        f"{name_rule}"
    )


def build_care_prompt(creature: Creature, care_type: str) -> list[dict[str, str]]:
    system = build_system_prompt(creature)
    if care_type == "feed":
        action_desc = "The person who cares for you just fed you."
    else:
        care_desc = care_type.replace("_", " ")
        action_desc = f"The person who cares for you just offered you {care_desc}."
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": f"{action_desc} Respond briefly with how you feel.",
        },
    ]


def build_talk_prompt(
    creature: Creature,
    user_message: str,
    recent_history: list[dict[str, str]],
) -> list[dict[str, str]]:
    system = build_system_prompt(creature)
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    for entry in recent_history:
        messages.append(entry)
    messages.append({"role": "user", "content": user_message})
    return messages


def build_reflection_prompt(creature: Creature) -> list[dict[str, str]]:
    system = build_system_prompt(creature)
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": (
                "Take a quiet moment. Reflect on how you feel right now, "
                "what you've noticed recently, or something you've been thinking about. "
                "Keep it very brief — just a thought or two."
            ),
        },
    ]


def build_rest_prompt(creature: Creature) -> list[dict[str, str]]:
    system = build_system_prompt(creature)
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": "You are about to rest. Say a brief, gentle farewell.",
        },
    ]

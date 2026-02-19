from __future__ import annotations

import string
from dataclasses import dataclass
from enum import StrEnum


class LifecycleStage(StrEnum):
    EGG = "egg"
    HATCHED = "hatched"
    JUVENILE = "juvenile"
    MATURE = "mature"
    RESTING = "resting"
    EXHAUSTED = "exhausted"


class DragonColour(StrEnum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    WHITE = "white"
    GOLD = "gold"

    @property
    def hex_tint(self) -> str:
        return _HEX_TINTS[self]

    @property
    def character_summary(self) -> str:
        return _CHARACTER_SUMMARIES[self]


_HEX_TINTS: dict[DragonColour, str] = {
    DragonColour.RED: "#E05252",
    DragonColour.GREEN: "#52A852",
    DragonColour.BLUE: "#5282E0",
    DragonColour.WHITE: "#C8C8D4",
    DragonColour.GOLD: "#D4A832",
}

_CHARACTER_SUMMARIES: dict[DragonColour, str] = {
    DragonColour.RED: "Bold and direct. Quick to react.",
    DragonColour.GREEN: "Inquisitive and observant. Drawn to novelty.",
    DragonColour.BLUE: "Gentle and attuned. Slow to trust but deeply loyal.",
    DragonColour.WHITE: "Calm and patient. Stable and slow to change.",
    DragonColour.GOLD: "Warm and sociable. Needs your attention.",
}


class CreatureName:
    """Immutable validated creature name (1-24 printable characters)."""

    __slots__ = ("_value",)
    _PRINTABLE = set(string.printable) - set(string.whitespace) | {" "}

    def __init__(self, raw: str) -> None:
        stripped = raw.strip()
        if not stripped:
            raise ValueError("Name must be at least 1 character")
        if len(stripped) > 24:
            raise ValueError("Name must be at most 24 characters")
        if not all(ch in self._PRINTABLE for ch in stripped):
            raise ValueError("Name must contain only printable characters")
        self._value = stripped

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"CreatureName({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CreatureName):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)


@dataclass(frozen=True)
class PersonalityProfile:
    seed: str
    trait_curiosity: float
    trait_sociability: float
    trait_confidence: float
    trait_emotional_sensitivity: float
    trait_autonomy_preference: float
    trait_loneliness_rate: float


@dataclass
class MoodState:
    mood: float
    energy: float
    trust: float
    trust_floor: float
    loneliness: float
    state_curiosity: float
    stability: float


@dataclass
class Creature:
    name: str
    colour: DragonColour
    personality: PersonalityProfile
    mood_state: MoodState
    lifecycle_stage: LifecycleStage
    pre_exhausted_stage: LifecycleStage | None
    pre_resting_stage: LifecycleStage | None
    born_at: float
    hatched_at: float | None
    public_key_hex: str
    cumulative_care_events: int
    cumulative_talk_interactions: int
    last_reflection_at: float | None


@dataclass(frozen=True)
class CreatureEvent:
    event_type: str
    from_stage: LifecycleStage | None
    to_stage: LifecycleStage | None
    created_at: float
    notes: str | None = None

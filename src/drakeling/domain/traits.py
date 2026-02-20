from __future__ import annotations

import random

from drakeling.domain.models import DragonColour, PersonalityProfile

COLOUR_TRAIT_BIAS: dict[DragonColour, dict[str, float]] = {
    DragonColour.RED: {
        "curiosity": 0.5, "sociability": 0.6, "confidence": 0.9,
        "emotional_sensitivity": 0.4, "autonomy_preference": 0.8,
        "loneliness_rate": 0.5,
    },
    DragonColour.GREEN: {
        "curiosity": 0.8, "sociability": 0.5, "confidence": 0.6,
        "emotional_sensitivity": 0.6, "autonomy_preference": 0.6,
        "loneliness_rate": 0.4,
    },
    DragonColour.BLUE: {
        "curiosity": 0.5, "sociability": 0.6, "confidence": 0.4,
        "emotional_sensitivity": 0.9, "autonomy_preference": 0.4,
        "loneliness_rate": 0.5,
    },
    DragonColour.WHITE: {
        "curiosity": 0.4, "sociability": 0.5, "confidence": 0.6,
        "emotional_sensitivity": 0.5, "autonomy_preference": 0.7,
        "loneliness_rate": 0.3,
    },
    DragonColour.GOLD: {
        "curiosity": 0.7, "sociability": 0.9, "confidence": 0.7,
        "emotional_sensitivity": 0.6, "autonomy_preference": 0.4,
        "loneliness_rate": 0.8,
    },
}

_VARIANCE = 0.15


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def generate_traits(colour: DragonColour, seed_hex: str) -> PersonalityProfile:
    """Generate a PersonalityProfile from a colour bias and a hex seed."""
    seed_bytes = bytes.fromhex(seed_hex)
    rng = random.Random(seed_bytes)
    bias = COLOUR_TRAIT_BIAS[colour]

    def sample(midpoint: float) -> float:
        return _clamp(midpoint + rng.uniform(-_VARIANCE, _VARIANCE))

    return PersonalityProfile(
        seed=seed_hex,
        trait_curiosity=sample(bias["curiosity"]),
        trait_sociability=sample(bias["sociability"]),
        trait_confidence=sample(bias["confidence"]),
        trait_emotional_sensitivity=sample(bias["emotional_sensitivity"]),
        trait_autonomy_preference=sample(bias["autonomy_preference"]),
        trait_loneliness_rate=sample(bias["loneliness_rate"]),
    )

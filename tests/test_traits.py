"""Tests for trait generation."""
import secrets

from openclaw_hatchling.domain.models import DragonColour
from openclaw_hatchling.domain.traits import COLOUR_TRAIT_BIAS, generate_traits


class TestColourTraitBias:
    def test_all_colours_present(self):
        for colour in DragonColour:
            assert colour in COLOUR_TRAIT_BIAS

    def test_six_traits_per_colour(self):
        for colour, bias in COLOUR_TRAIT_BIAS.items():
            assert len(bias) == 6, f"{colour} has {len(bias)} traits"

    def test_bias_values_in_range(self):
        for colour, bias in COLOUR_TRAIT_BIAS.items():
            for trait, value in bias.items():
                assert 0.0 <= value <= 1.0, f"{colour}.{trait} = {value}"


class TestGenerateTraits:
    def test_returns_personality_profile(self):
        seed = secrets.token_bytes(32).hex()
        profile = generate_traits(DragonColour.GOLD, seed)
        assert profile.seed == seed

    def test_traits_in_range(self):
        seed = secrets.token_bytes(32).hex()
        profile = generate_traits(DragonColour.RED, seed)
        for field in [
            "trait_curiosity", "trait_sociability", "trait_confidence",
            "trait_emotional_sensitivity", "trait_autonomy_preference",
            "trait_loneliness_rate",
        ]:
            value = getattr(profile, field)
            assert 0.0 <= value <= 1.0, f"{field} = {value}"

    def test_deterministic_from_seed(self):
        seed = secrets.token_bytes(32).hex()
        p1 = generate_traits(DragonColour.BLUE, seed)
        p2 = generate_traits(DragonColour.BLUE, seed)
        assert p1 == p2

    def test_different_seeds_differ(self):
        s1 = secrets.token_bytes(32).hex()
        s2 = secrets.token_bytes(32).hex()
        p1 = generate_traits(DragonColour.GREEN, s1)
        p2 = generate_traits(DragonColour.GREEN, s2)
        assert p1 != p2

    def test_different_colours_differ(self):
        seed = secrets.token_bytes(32).hex()
        p1 = generate_traits(DragonColour.RED, seed)
        p2 = generate_traits(DragonColour.WHITE, seed)
        # Traits should differ because bias midpoints differ
        assert p1.trait_confidence != p2.trait_confidence

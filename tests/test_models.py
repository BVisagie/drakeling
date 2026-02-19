"""Tests for domain models."""
import pytest

from openclaw_hatchling.domain.models import (
    CreatureEvent,
    CreatureName,
    DragonColour,
    LifecycleStage,
    MoodState,
    PersonalityProfile,
)


class TestDragonColour:
    def test_all_five_colours_exist(self):
        assert len(DragonColour) == 5

    def test_hex_tints_are_valid(self):
        for colour in DragonColour:
            assert colour.hex_tint.startswith("#")
            assert len(colour.hex_tint) == 7

    def test_character_summaries_non_empty(self):
        for colour in DragonColour:
            assert len(colour.character_summary) > 0


class TestLifecycleStage:
    def test_all_six_stages_exist(self):
        assert len(LifecycleStage) == 6

    def test_values_are_lowercase(self):
        for stage in LifecycleStage:
            assert stage.value == stage.value.lower()


class TestCreatureName:
    def test_valid_name(self):
        name = CreatureName("Ember")
        assert name.value == "Ember"

    def test_strips_whitespace(self):
        name = CreatureName("  Spark  ")
        assert name.value == "Spark"

    def test_empty_name_rejected(self):
        with pytest.raises(ValueError, match="at least 1"):
            CreatureName("")

    def test_whitespace_only_rejected(self):
        with pytest.raises(ValueError, match="at least 1"):
            CreatureName("   ")

    def test_too_long_rejected(self):
        with pytest.raises(ValueError, match="at most 24"):
            CreatureName("A" * 25)

    def test_max_length_accepted(self):
        name = CreatureName("A" * 24)
        assert len(name.value) == 24

    def test_control_chars_rejected(self):
        with pytest.raises(ValueError, match="printable"):
            CreatureName("hello\x00world")

    def test_equality(self):
        assert CreatureName("Ember") == CreatureName("Ember")
        assert CreatureName("Ember") != CreatureName("Blaze")

    def test_str(self):
        assert str(CreatureName("Ember")) == "Ember"


class TestMoodState:
    def test_defaults(self):
        ms = MoodState(
            mood=0.5, energy=0.5, trust=0.5, trust_floor=0.0,
            loneliness=0.0, state_curiosity=0.5, stability=0.5,
        )
        assert ms.mood == 0.5
        assert ms.loneliness == 0.0


class TestCreatureEvent:
    def test_frozen(self):
        event = CreatureEvent(
            event_type="born",
            from_stage=None,
            to_stage=LifecycleStage.EGG,
            created_at=1000.0,
        )
        assert event.notes is None
        assert event.event_type == "born"

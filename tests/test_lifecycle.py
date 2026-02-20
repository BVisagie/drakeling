"""Tests for lifecycle transition evaluation."""
import time

from drakeling.domain.lifecycle import (
    EGG_TO_HATCHED_CARE,
    EGG_TO_HATCHED_TIME,
    ENERGY_RESTING_THRESHOLD,
    ENERGY_WAKE_THRESHOLD,
    HATCHED_TO_JUVENILE_CARE,
    HATCHED_TO_JUVENILE_TIME,
    JUVENILE_TO_MATURE_CARE,
    JUVENILE_TO_MATURE_TALK,
    JUVENILE_TO_MATURE_TIME,
    evaluate_transitions,
)
from drakeling.domain.models import (
    Creature,
    LifecycleStage,
    MoodState,
    PersonalityProfile,
)


def _make_creature(
    stage: LifecycleStage = LifecycleStage.EGG,
    born_at: float = 0.0,
    hatched_at: float | None = None,
    care: int = 0,
    talk: int = 0,
    energy: float = 0.5,
    pre_resting_stage: LifecycleStage | None = None,
) -> Creature:
    return Creature(
        name="Test",
        colour="red",
        personality=PersonalityProfile(
            seed="aa" * 32,
            trait_curiosity=0.5, trait_sociability=0.5, trait_confidence=0.5,
            trait_emotional_sensitivity=0.5, trait_autonomy_preference=0.5,
            trait_loneliness_rate=0.5,
        ),
        mood_state=MoodState(
            mood=0.5, energy=energy, trust=0.5, trust_floor=0.0,
            loneliness=0.0, state_curiosity=0.5, stability=0.5,
        ),
        lifecycle_stage=stage,
        pre_exhausted_stage=None,
        pre_resting_stage=pre_resting_stage,
        born_at=born_at,
        hatched_at=hatched_at,
        public_key_hex="ab" * 32,
        cumulative_care_events=care,
        cumulative_talk_interactions=talk,
        last_reflection_at=None,
    )


class TestEggToHatched:
    def test_no_transition_too_early(self):
        c = _make_creature(care=1, born_at=100.0)
        assert evaluate_transitions(c, now=100.0 + EGG_TO_HATCHED_TIME - 1) is None

    def test_no_transition_no_care(self):
        c = _make_creature(care=0, born_at=0.0)
        assert evaluate_transitions(c, now=EGG_TO_HATCHED_TIME + 1) is None

    def test_transitions_when_ready(self):
        c = _make_creature(care=EGG_TO_HATCHED_CARE, born_at=0.0)
        event = evaluate_transitions(c, now=EGG_TO_HATCHED_TIME + 1)
        assert event is not None
        assert event.event_type == "egg_to_hatched"
        assert event.to_stage == LifecycleStage.HATCHED


class TestHatchedToJuvenile:
    def test_transitions_when_ready(self):
        c = _make_creature(
            stage=LifecycleStage.HATCHED,
            hatched_at=0.0,
            care=HATCHED_TO_JUVENILE_CARE,
        )
        event = evaluate_transitions(c, now=HATCHED_TO_JUVENILE_TIME + 1)
        assert event is not None
        assert event.event_type == "hatched_to_juvenile"

    def test_no_transition_not_enough_care(self):
        c = _make_creature(
            stage=LifecycleStage.HATCHED,
            hatched_at=0.0,
            care=HATCHED_TO_JUVENILE_CARE - 1,
        )
        assert evaluate_transitions(c, now=HATCHED_TO_JUVENILE_TIME + 1) is None


class TestJuvenileToMature:
    def test_transitions_when_ready(self):
        c = _make_creature(
            stage=LifecycleStage.JUVENILE,
            hatched_at=0.0,
            care=JUVENILE_TO_MATURE_CARE,
            talk=JUVENILE_TO_MATURE_TALK,
        )
        event = evaluate_transitions(c, now=JUVENILE_TO_MATURE_TIME + 1)
        assert event is not None
        assert event.event_type == "juvenile_to_mature"

    def test_no_transition_not_enough_talk(self):
        c = _make_creature(
            stage=LifecycleStage.JUVENILE,
            hatched_at=0.0,
            care=JUVENILE_TO_MATURE_CARE,
            talk=JUVENILE_TO_MATURE_TALK - 1,
        )
        assert evaluate_transitions(c, now=JUVENILE_TO_MATURE_TIME + 1) is None


class TestMatureToResting:
    def test_low_energy_triggers_resting(self):
        c = _make_creature(
            stage=LifecycleStage.MATURE,
            energy=ENERGY_RESTING_THRESHOLD - 0.01,
        )
        event = evaluate_transitions(c, now=time.time())
        assert event is not None
        assert event.event_type == "entered_resting"

    def test_normal_energy_no_transition(self):
        c = _make_creature(stage=LifecycleStage.MATURE, energy=0.5)
        assert evaluate_transitions(c, now=time.time()) is None


class TestRestingWake:
    def test_wake_on_energy_recovery(self):
        c = _make_creature(
            stage=LifecycleStage.RESTING,
            energy=ENERGY_WAKE_THRESHOLD,
            pre_resting_stage=LifecycleStage.MATURE,
        )
        event = evaluate_transitions(c, now=time.time(), resting_entered_at=0.0)
        assert event is not None
        assert event.event_type == "exited_resting"
        assert event.to_stage == LifecycleStage.MATURE

    def test_wake_on_timeout(self):
        c = _make_creature(
            stage=LifecycleStage.RESTING,
            energy=0.2,
            pre_resting_stage=LifecycleStage.JUVENILE,
        )
        event = evaluate_transitions(c, now=4000.0, resting_entered_at=0.0)
        assert event is not None
        assert event.event_type == "exited_resting"
        assert event.to_stage == LifecycleStage.JUVENILE

"""Tests for stat decay and boost functions."""
from openclaw_hatchling.domain.decay import (
    apply_care_boost,
    apply_talk_boost,
    apply_tick_decay,
)
from openclaw_hatchling.domain.models import LifecycleStage, MoodState, PersonalityProfile


def _make_mood(**overrides) -> MoodState:
    defaults = dict(
        mood=0.5, energy=0.5, trust=0.5, trust_floor=0.0,
        loneliness=0.0, state_curiosity=0.5, stability=0.5,
    )
    defaults.update(overrides)
    return MoodState(**defaults)


def _make_traits(**overrides) -> PersonalityProfile:
    defaults = dict(
        seed="aa" * 32,
        trait_curiosity=0.5, trait_sociability=0.5, trait_confidence=0.5,
        trait_emotional_sensitivity=0.5, trait_autonomy_preference=0.5,
        trait_loneliness_rate=0.5,
    )
    defaults.update(overrides)
    return PersonalityProfile(**defaults)


class TestTickDecay:
    def test_mood_decays(self):
        ms = _make_mood(mood=0.5)
        result = apply_tick_decay(ms, LifecycleStage.MATURE, _make_traits())
        assert result.mood < 0.5

    def test_energy_decays_normally(self):
        ms = _make_mood(energy=0.5)
        result = apply_tick_decay(ms, LifecycleStage.MATURE, _make_traits())
        assert result.energy < 0.5

    def test_energy_recovers_during_resting(self):
        ms = _make_mood(energy=0.3)
        result = apply_tick_decay(ms, LifecycleStage.RESTING, _make_traits())
        assert result.energy > 0.3

    def test_loneliness_grows(self):
        ms = _make_mood(loneliness=0.0)
        result = apply_tick_decay(ms, LifecycleStage.MATURE, _make_traits())
        assert result.loneliness > 0.0

    def test_loneliness_rate_affects_growth(self):
        ms = _make_mood(loneliness=0.0)
        low_rate = _make_traits(trait_loneliness_rate=0.3)
        high_rate = _make_traits(trait_loneliness_rate=0.8)
        low_result = apply_tick_decay(ms, LifecycleStage.MATURE, low_rate)
        high_result = apply_tick_decay(ms, LifecycleStage.MATURE, high_rate)
        assert high_result.loneliness > low_result.loneliness

    def test_gold_loneliness_rate(self):
        ms = _make_mood(loneliness=0.0)
        gold_traits = _make_traits(trait_loneliness_rate=0.8)
        result = apply_tick_decay(ms, LifecycleStage.MATURE, gold_traits)
        expected = 0.008 * (0.5 + 0.8)
        assert abs(result.loneliness - expected) < 1e-9

    def test_trust_never_below_floor(self):
        ms = _make_mood(trust=0.3, trust_floor=0.3)
        result = apply_tick_decay(ms, LifecycleStage.MATURE, _make_traits())
        assert result.trust >= 0.3

    def test_stability_grows_during_resting(self):
        ms = _make_mood(stability=0.5)
        result = apply_tick_decay(ms, LifecycleStage.RESTING, _make_traits())
        assert result.stability > 0.5

    def test_all_values_clamped(self):
        ms = _make_mood(mood=0.001, energy=0.001, trust=0.0, loneliness=0.99,
                        state_curiosity=0.001, stability=0.001)
        result = apply_tick_decay(ms, LifecycleStage.MATURE, _make_traits())
        for field in ["mood", "energy", "trust", "loneliness", "state_curiosity", "stability"]:
            val = getattr(result, field)
            assert 0.0 <= val <= 1.0, f"{field} = {val}"


class TestCareBoost:
    def test_mood_increases(self):
        ms = _make_mood(mood=0.5)
        result = apply_care_boost(ms)
        assert result.mood > 0.5

    def test_loneliness_resets(self):
        ms = _make_mood(loneliness=0.8)
        result = apply_care_boost(ms)
        assert result.loneliness == 0.0


class TestTalkBoost:
    def test_mood_increases(self):
        ms = _make_mood(mood=0.5)
        result = apply_talk_boost(ms, _make_traits())
        assert result.mood > 0.5

    def test_trust_increases(self):
        ms = _make_mood(trust=0.5)
        result = apply_talk_boost(ms, _make_traits())
        assert result.trust > 0.5

    def test_loneliness_resets(self):
        ms = _make_mood(loneliness=0.7)
        result = apply_talk_boost(ms, _make_traits())
        assert result.loneliness == 0.0

    def test_trust_floor_rises_when_trust_high(self):
        ms = _make_mood(trust=0.79, trust_floor=0.0)
        result = apply_talk_boost(ms, _make_traits())
        # trust 0.79 + 0.02 = 0.81 > 0.8, so floor should rise
        assert result.trust_floor > 0.0

    def test_curiosity_boosted_by_trait(self):
        ms = _make_mood(state_curiosity=0.3)
        low = _make_traits(trait_curiosity=0.2)
        high = _make_traits(trait_curiosity=0.9)
        r_low = apply_talk_boost(ms, low)
        r_high = apply_talk_boost(ms, high)
        assert r_high.state_curiosity > r_low.state_curiosity

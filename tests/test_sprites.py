"""Tests for sprite inventory."""
from drakeling.domain.models import DragonColour, LifecycleStage
from drakeling.domain.sprites import get_sprite


class TestSprites:
    def test_all_30_combinations_accessible(self):
        count = 0
        for stage in LifecycleStage:
            for colour in DragonColour:
                sprite = get_sprite(stage, colour)
                assert isinstance(sprite, str)
                assert len(sprite) > 0
                count += 1
        assert count == 30

    def test_sprites_have_reasonable_dimensions(self):
        for stage in LifecycleStage:
            for colour in DragonColour:
                sprite = get_sprite(stage, colour)
                lines = sprite.strip().split("\n")
                assert 6 <= len(lines) <= 14, (
                    f"{stage}/{colour}: {len(lines)} lines"
                )
                for line in lines:
                    assert len(line) <= 25, (
                        f"{stage}/{colour}: line too wide ({len(line)} chars)"
                    )

    def test_monochrome_graceful_degradation(self):
        """Sprites must render correctly without colour markup."""
        for stage in LifecycleStage:
            for colour in DragonColour:
                sprite = get_sprite(stage, colour)
                # Should contain only printable ASCII + whitespace
                for ch in sprite:
                    assert ch.isprintable() or ch in ("\n", "\r"), (
                        f"{stage}/{colour}: non-printable char {ch!r}"
                    )

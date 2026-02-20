from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Static

from drakeling.domain.models import DragonColour, LifecycleStage
from drakeling.domain.sprites import get_sprite


def _desaturate_hex(hex_colour: str) -> str:
    """Shift a hex colour toward grey for the exhausted stage."""
    hex_colour = hex_colour.lstrip("#")
    r, g, b = int(hex_colour[:2], 16), int(hex_colour[2:4], 16), int(hex_colour[4:], 16)
    grey = (r + g + b) // 3
    r = (r + grey) // 2
    g = (g + grey) // 2
    b = (b + grey) // 2
    return f"#{r:02x}{g:02x}{b:02x}"


class SpritePanel(Vertical):
    """Displays the creature sprite with colour tinting and stage label."""

    DEFAULT_CSS = """
    SpritePanel {
        height: auto;
        padding: 1 2;
    }
    """

    def __init__(
        self,
        name: str,
        stage: LifecycleStage,
        colour: DragonColour,
    ) -> None:
        super().__init__()
        self._creature_name = name
        self._stage = stage
        self._colour = colour

    def compose(self) -> ComposeResult:
        yield Static(id="sprite-art")
        yield Label(id="stage-label")

    def on_mount(self) -> None:
        self.update_sprite(self._stage, self._colour)
        self.border_title = self._creature_name

    def update_sprite(self, stage: LifecycleStage, colour: DragonColour) -> None:
        self._stage = stage
        self._colour = colour
        art = get_sprite(stage, colour)
        hex_tint = colour.hex_tint
        if stage == LifecycleStage.EXHAUSTED:
            hex_tint = _desaturate_hex(hex_tint)

        sprite = self.query_one("#sprite-art", Static)
        sprite.update(f"[{hex_tint}]{art}[/]")

        label = self.query_one("#stage-label", Label)
        label.update(f"  {stage.value}")

        self.styles.border = ("round", hex_tint)
        self.border_title = self._creature_name

from __future__ import annotations

import random
import string
from typing import ClassVar

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Input, Label, Static

from drakeling.domain.models import DragonColour, LifecycleStage
from drakeling.domain.sprites import get_sprite
from drakeling.ui.client import DrakelingClient


class BirthScreen(Screen):
    """Full-screen birth ceremony."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("r", "reroll", "Reroll colour"),
        Binding("enter", "confirm", "Confirm"),
    ]

    def __init__(self, client: DrakelingClient) -> None:
        super().__init__()
        self._client = client
        self._colour: DragonColour = random.choice(list(DragonColour))
        self._rerolls_remaining = 3
        self._colour_confirmed = False
        self._name: str | None = None
        self._phase: str = "egg"  # egg -> naming -> confirm -> done

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="birth-container"):
                yield Static(id="egg-sprite")
                yield Label(id="colour-label")
                yield Label(id="character-label")
                yield Label(id="reroll-label")
                yield Label(id="prompt-label")
        yield Footer()

    def on_mount(self) -> None:
        self._update_egg_display()

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        """Control which bindings are active/visible per phase."""
        if action == "reroll":
            if self._phase != "egg" or self._rerolls_remaining <= 0:
                return None  # hide
            return True
        if action == "confirm":
            if self._phase in ("egg", "confirm"):
                return True
            return None  # hide during naming and done
        return True

    def _update_egg_display(self) -> None:
        hex_tint = self._colour.hex_tint
        sprite = self.query_one("#egg-sprite", Static)
        egg_art = get_sprite(LifecycleStage.EGG, self._colour)
        sprite.update(f"[{hex_tint}]{egg_art}[/]")

        colour_label = self.query_one("#colour-label", Label)
        colour_label.update(f"[{hex_tint}]{self._colour.value}[/]")

        char_label = self.query_one("#character-label", Label)
        char_label.update(self._colour.character_summary)

        reroll_label = self.query_one("#reroll-label", Label)
        if self._colour_confirmed:
            reroll_label.display = False
        elif self._rerolls_remaining > 0:
            reroll_label.update(
                f"[dim]{self._rerolls_remaining} reroll{'s' if self._rerolls_remaining != 1 else ''} remaining[/]"
            )
        else:
            reroll_label.update("[dim]No rerolls remaining[/]")

        prompt_label = self.query_one("#prompt-label", Label)
        if not self._colour_confirmed:
            prompt_label.update("[bold]Enter[/] to keep this colour")

    def action_reroll(self) -> None:
        if self._colour_confirmed or self._rerolls_remaining <= 0:
            return
        self._rerolls_remaining -= 1
        self._colour = random.choice(list(DragonColour))
        self._update_egg_display()
        self.refresh_bindings()

    def action_confirm(self) -> None:
        if self._phase == "egg" and not self._colour_confirmed:
            self._colour_confirmed = True
            self._phase = "naming"
            self._update_egg_display()
            self.query_one("#reroll-label", Label).display = False

            prompt_label = self.query_one("#prompt-label", Label)
            prompt_label.update("What will you call them?")

            name_input = Input(
                placeholder="Name (1–24 characters)",
                id="name-input",
                max_length=24,
            )
            self.query_one("#birth-container", Vertical).mount(name_input)
            name_input.focus()
            self.refresh_bindings()
            return

        if self._phase == "confirm":
            self._phase = "done"
            self.refresh_bindings()
            self.run_worker(self._do_birth())

    @on(Input.Submitted, "#name-input")
    def _on_name_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        if not raw:
            return
        printable = set(string.printable) - set(string.whitespace) | {" "}
        if not all(ch in printable for ch in raw):
            return
        if len(raw) > 24:
            return

        self._name = raw
        self._phase = "confirm"

        name_input = self.query_one("#name-input", Input)
        name_input.remove()

        hex_tint = self._colour.hex_tint
        self.query_one("#prompt-label", Label).update(
            f"A [{hex_tint}]{self._colour.value}[/] Hatchling named [bold]{self._name}[/].\n\n"
            "Press [bold]Enter[/] to begin."
        )
        self.query_one("#character-label", Label).display = False
        self.set_focus(None)
        self.refresh_bindings()

    async def _do_birth(self) -> None:
        try:
            await self._client.birth(self._colour.value, self._name or "")
        except Exception as exc:
            self.query_one("#prompt-label", Label).update(f"Birth failed: {exc}")
            self._phase = "confirm"
            return

        self.query_one("#prompt-label", Label).update(
            "[bold]Your Hatchling is here.[/]"
        )
        import asyncio
        await asyncio.sleep(1.5)
        # Fetch status before dismissing so the callback can push MainScreen
        # immediately, avoiding a black screen gap.
        status = await self._client.get_status()
        self.dismiss(status)

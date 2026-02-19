from __future__ import annotations

from textual.widgets import RichLog


class InteractionFeed(RichLog):
    """Scrollable log of creature expressions and interactions."""

    DEFAULT_CSS = """
    InteractionFeed {
        height: 1fr;
        border: round $secondary;
        padding: 0 1;
    }
    """

    def add_creature_message(self, text: str, colour_hex: str = "") -> None:
        if colour_hex:
            self.write(f"[{colour_hex}]> {text}[/]")
        else:
            self.write(f"> {text}")

    def add_user_message(self, text: str) -> None:
        self.write(f"[dim]you:[/] {text}")

    def add_system_note(self, text: str) -> None:
        self.write(f"[dim italic]{text}[/]")

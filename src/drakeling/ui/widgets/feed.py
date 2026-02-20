from __future__ import annotations

from rich.markup import escape
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

    def __init__(self, **kwargs: object) -> None:
        super().__init__(markup=True, **kwargs)

    def add_creature_message(self, text: str, colour_hex: str = "") -> None:
        safe = escape(text)
        if colour_hex:
            self.write(f"[{colour_hex}]> {safe}[/]")
        else:
            self.write(f"> {safe}")

    def add_user_message(self, text: str) -> None:
        self.write(f"[dim]you:[/] {escape(text)}")

    def add_system_note(self, text: str) -> None:
        self.write(f"[dim italic]{escape(text)}[/]")

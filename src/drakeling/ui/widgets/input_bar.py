from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Input, Label


class InputBar(Horizontal):
    """Text input for talking to the creature."""

    DEFAULT_CSS = """
    InputBar {
        height: 3;
        dock: bottom;
        padding: 0 1;
    }
    InputBar Input {
        width: 1fr;
    }
    InputBar Label {
        width: auto;
        padding: 1 1 0 1;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Talk to your creature...", id="talk-input")

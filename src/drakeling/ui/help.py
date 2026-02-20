"""F1 help overlay explaining actions and stats in plain language."""
from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static

HELP_TEXT = """\
[bold underline]Drakeling — Quick Guide[/]

[bold]Your creature is not an assistant.[/]
It reflects, learns about you, and expresses its feelings.
Talk to it, care for it, and let it rest when it needs to.

[bold underline]Actions[/]

  [bold]F1  Help[/]        This screen.
                    (? if F-keys don't work in your terminal)

  [bold]F2  Care[/]        Show gentle attention.
                    Lifts mood and eases loneliness.

  [bold]F3  Rest[/]        Put your creature to sleep.
                    Rest recovers energy and stability.
                    It wakes on its own when ready.

  [bold]F4  Talk[/]        Focus the text input (Ctrl+T works too).
                    Type a message and press Enter.
                    Talking lifts mood, builds trust,
                    sparks curiosity, and eases loneliness.

  [bold]F5  Feed[/]        Feed your creature (Ctrl+F works too).
                    Boosts energy and mood,
                    and eases loneliness.

[bold underline]Stats[/]

  [bold]Mood[/]            How your creature feels right now.
                    Improves with care, talking, and feeding.

  [bold]Energy[/]          Physical stamina. Decays over time.
                    Feeding gives a boost; resting recovers it fully.

  [bold]Trust[/]           Built through conversation over time.
                    A rising floor means trust can never fall
                    below what you have earned together.

  [bold]Loneliness[/]      Grows when you are away.
                    Any interaction resets it to zero.

  [bold]Curiosity[/]       Sparked by conversation.
                    Fades between talks, stronger for
                    naturally curious creatures.

  [bold]Stability[/]       Inner balance. Only recovers during rest.
                    Let your creature sleep to restore it.

[dim]Press any key to close.[/]

[dim]In embedded terminals (Zed, VS Code, etc.), F-keys may not work.
Use ? for Help, Ctrl+T for Talk, Ctrl+F for Feed.[/]
"""


class HelpScreen(ModalScreen[None]):
    """Dismissable help overlay."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("escape", "dismiss_help", "Close", show=False),
    ]

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    #help-container {
        width: 60;
        max-height: 80%;
        background: $surface;
        border: round $primary;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        with Center():
            with VerticalScroll(id="help-container"):
                yield Static(HELP_TEXT)

    def on_key(self) -> None:
        self.dismiss(None)

    def action_dismiss_help(self) -> None:
        self.dismiss(None)

from __future__ import annotations

import time
from typing import ClassVar

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Label, Static

from drakeling.domain.models import DragonColour
from drakeling.ui.client import DrakelingClient


def _format_age(born_at: float) -> str:
    elapsed = max(0, time.time() - born_at)
    days = int(elapsed // 86400)
    hours = int((elapsed % 86400) // 3600)
    minutes = int((elapsed % 3600) // 60)
    if days > 0:
        return f"{days}d {hours}h"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


class ReleaseSummaryScreen(Screen):
    """Farewell summary of the creature before release confirmation."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("enter", "proceed", "Continue"),
        Binding("escape", "cancel", "Go back"),
    ]

    DEFAULT_CSS = """
    ReleaseSummaryScreen {
        align: center middle;
    }
    #release-summary {
        width: 50;
        height: auto;
        padding: 1 2;
    }
    #summary-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    .summary-stat {
        margin-left: 2;
    }
    #summary-prompt {
        text-align: center;
        margin-top: 1;
    }
    """

    def __init__(self, client: DrakelingClient, status: dict) -> None:
        super().__init__()
        self._client = client
        self._status = status

    def compose(self) -> ComposeResult:
        s = self._status
        colour = DragonColour(s["colour"])
        hex_tint = colour.hex_tint
        name = s["name"]
        stage = s.get("lifecycle_stage", "unknown").replace("_", " ")
        age = _format_age(s.get("born_at", time.time()))
        care = s.get("cumulative_care_events", 0)
        talks = s.get("cumulative_talk_interactions", 0)
        trust = s.get("trust", 0.0)
        trust_pct = f"{trust * 100:.0f}%"

        with Center():
            with Vertical(id="release-summary"):
                yield Static(
                    f"[bold]Farewell, [{hex_tint}]{name}[/][/]",
                    id="summary-title",
                )
                yield Label(f"  Colour      [{hex_tint}]{colour.value}[/]", classes="summary-stat")
                yield Label(f"  Stage       {stage}", classes="summary-stat")
                yield Label(f"  Age         {age}", classes="summary-stat")
                yield Label(f"  Care given  {care} time{'s' if care != 1 else ''}", classes="summary-stat")
                yield Label(f"  Talks       {talks} conversation{'s' if talks != 1 else ''}", classes="summary-stat")
                yield Label(f"  Trust       {trust_pct}", classes="summary-stat")
                yield Static(
                    "\n[dim]Enter[/] to continue  ·  [dim]Escape[/] to go back",
                    id="summary-prompt",
                )
        yield Footer()

    def action_proceed(self) -> None:
        self.app.push_screen(
            ReleaseConfirmScreen(self._client, self._status),
            callback=self._on_confirm_result,
        )

    def _on_confirm_result(self, result: object = None) -> None:
        if result == "released":
            self.dismiss("released")

    def action_cancel(self) -> None:
        self.dismiss(None)


class ReleaseConfirmScreen(Screen):
    """Final confirmation before irreversible release."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("enter", "confirm", "Release forever"),
        Binding("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    ReleaseConfirmScreen {
        align: center middle;
    }
    #release-confirm {
        width: 50;
        height: auto;
        padding: 1 2;
    }
    #confirm-message {
        text-align: center;
    }
    #confirm-prompt {
        text-align: center;
        margin-top: 1;
    }
    """

    def __init__(self, client: DrakelingClient, status: dict) -> None:
        super().__init__()
        self._client = client
        self._name = status["name"]

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="release-confirm"):
                yield Static(
                    f"[bold red]Release {self._name} forever?[/]\n\n"
                    "This cannot be undone.",
                    id="confirm-message",
                )
                yield Static(
                    "\n[dim]Enter[/] to release  ·  [dim]Escape[/] to cancel",
                    id="confirm-prompt",
                )
        yield Footer()

    def action_confirm(self) -> None:
        self._do_release()

    @work(thread=False)
    async def _do_release(self) -> None:
        try:
            await self._client.release()
        except Exception as exc:
            self.query_one("#confirm-message", Static).update(
                f"[bold red]Release failed:[/] {exc}"
            )
            return
        self.dismiss("released")

    def action_cancel(self) -> None:
        self.dismiss(None)

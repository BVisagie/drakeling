from __future__ import annotations

from typing import ClassVar

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label, Static

from drakeling.domain.models import DragonColour, LifecycleStage
from drakeling.ui.client import DaemonNotAvailable, DrakelingClient
from drakeling.ui.widgets.feed import InteractionFeed
from drakeling.ui.widgets.input_bar import InputBar
from drakeling.ui.widgets.sprite_panel import SpritePanel
from drakeling.ui.widgets.stats_display import StatsDisplay


class DaemonUnavailableScreen(Screen):
    """Shown when the daemon is not running or not yet initialised."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("r", "retry", "Retry"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, reason: str) -> None:
        super().__init__()
        self._reason = reason

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical():
                yield Static(
                    "[bold]Could not connect to the Drakeling daemon.[/]\n\n"
                    f"{self._reason}\n\n"
                    "1. Start the daemon first:\n\n"
                    "   [bold green]drakelingd[/]\n\n"
                    "2. Then run this again:\n\n"
                    "   [bold green]drakeling[/]\n\n"
                    "Press [bold]R[/] to retry  ·  [bold]Q[/] to quit",
                    id="error-message",
                )
        yield Footer()

    def action_retry(self) -> None:
        self.dismiss("retry")

    def action_quit(self) -> None:
        self.app.exit()


class MainScreen(Screen):
    """Primary creature status and interaction screen."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("f2", "care_menu", "Care"),
        Binding("f3", "rest", "Rest"),
        Binding("f4", "focus_input", "Talk"),
        Binding("f8", "release", "Release"),
        Binding("q", "quit", "Quit"),
    ]

    DEFAULT_CSS = """
    MainScreen {
        layout: grid;
        grid-size: 2 2;
        grid-rows: auto 1fr;
    }
    #left-panel {
        row-span: 2;
        width: 30;
    }
    #right-top {
        height: auto;
    }
    #right-bottom {
        height: 1fr;
    }
    """

    def __init__(self, client: DrakelingClient, status: dict) -> None:
        super().__init__()
        self._client = client
        self._status = status
        self._colour = DragonColour(status["colour"])
        self._stage = LifecycleStage(status["lifecycle_stage"])

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="left-panel"):
            yield SpritePanel(
                name=self._status["name"],
                stage=self._stage,
                colour=self._colour,
            )
            yield StatsDisplay(id="stats")
        with Vertical(id="right-top"):
            yield Label("", id="attention-indicator")
        with Vertical(id="right-bottom"):
            yield InteractionFeed(id="feed")
            yield InputBar()
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_stats()
        self._poll_status()
        talk_input = self.query_one("#talk-input", Input)
        talk_input.focus()

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        if action == "quit":
            talk_input = self.query_one("#talk-input", Input)
            if talk_input.has_focus:
                return None
        return True

    def _refresh_stats(self) -> None:
        stats = self.query_one("#stats", StatsDisplay)
        s = self._status
        stats.update_stats(
            mood=s.get("mood", 0.5),
            energy=s.get("energy", 0.5),
            trust=s.get("trust", 0.5),
            loneliness=s.get("loneliness", 0.0),
            state_curiosity=s.get("state_curiosity", 0.5),
            stability=s.get("stability", 0.5),
        )
        self._stage = LifecycleStage(s.get("lifecycle_stage", "egg"))
        sprite = self.query_one(SpritePanel)
        sprite.update_sprite(self._stage, self._colour)

    @work(exclusive=True, thread=False)
    async def _poll_status(self) -> None:
        """Periodically refresh status from daemon."""
        import asyncio
        while True:
            await asyncio.sleep(5)
            try:
                new_status = await self._client.get_status()
                if new_status:
                    self._status = new_status
                    self._refresh_stats()

                attn = await self._client.needs_attention()
                indicator = self.query_one("#attention-indicator", Label)
                if attn and attn.get("needs_attention"):
                    reason = attn.get("reason", "")
                    indicator.update(f"[bold red]! {reason.replace('_', ' ')}[/]")
                else:
                    indicator.update("")
            except Exception:
                pass

    @on(Input.Submitted, "#talk-input")
    def _on_talk(self, event: Input.Submitted) -> None:
        message = event.value.strip()
        if not message:
            return
        event.input.clear()
        feed = self.query_one("#feed", InteractionFeed)
        feed.add_user_message(message)
        self._do_talk(message)

    @work(thread=False)
    async def _do_talk(self, message: str) -> None:
        feed = self.query_one("#feed", InteractionFeed)
        try:
            result = await self._client.talk(message)
            response = result.get("response")
            if response:
                feed.add_creature_message(response, self._colour.hex_tint)
            elif result.get("budget_exhausted"):
                feed.add_system_note("(resting quietly for now)")
            if "state" in result:
                self._status.update(result["state"])
                self._refresh_stats()
        except Exception as exc:
            feed.add_system_note(f"(could not reach daemon: {exc})")

    def action_care_menu(self) -> None:
        self._do_care("gentle_attention")

    @work(thread=False)
    async def _do_care(self, care_type: str) -> None:
        feed = self.query_one("#feed", InteractionFeed)
        feed.add_system_note(f"you offer {care_type.replace('_', ' ')}...")
        try:
            result = await self._client.care(care_type)
            response = result.get("response")
            if response:
                feed.add_creature_message(response, self._colour.hex_tint)
            if "state" in result:
                self._status.update(result["state"])
                self._refresh_stats()
        except Exception as exc:
            feed.add_system_note(f"(could not reach daemon: {exc})")

    def action_rest(self) -> None:
        self._do_rest()

    @work(thread=False)
    async def _do_rest(self) -> None:
        feed = self.query_one("#feed", InteractionFeed)
        try:
            result = await self._client.rest()
            response = result.get("response")
            if response:
                feed.add_creature_message(response, self._colour.hex_tint)
            feed.add_system_note("your creature is resting")
        except Exception as exc:
            feed.add_system_note(f"(could not rest: {exc})")

    def action_focus_input(self) -> None:
        self.query_one("#talk-input", Input).focus()

    def action_release(self) -> None:
        from drakeling.ui.release import ReleaseSummaryScreen

        self.app.push_screen(
            ReleaseSummaryScreen(self._client, self._status),
            callback=self._on_release_result,
        )

    def _on_release_result(self, result: object = None) -> None:
        if result == "released":
            self.dismiss("released")


class HatchlingApp(App):
    """Terminal UI entry point for Drakeling."""

    TITLE = "Drakeling"

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._client = DrakelingClient()

    async def on_mount(self) -> None:
        await self._try_connect()

    async def _try_connect(self) -> None:
        """Attempt to reach the daemon; show error screen or proceed."""
        self._client.reload_token()

        if not self._client.has_token:
            self.push_screen(
                DaemonUnavailableScreen(
                    "No API token found — the daemon has not been started yet."
                ),
                callback=self._on_error_dismissed,
            )
            return

        reachable = await self._client.ping()
        if not reachable:
            self.push_screen(
                DaemonUnavailableScreen(
                    "The daemon is not responding on "
                    f"{self._client._base_url}."
                ),
                callback=self._on_error_dismissed,
            )
            return

        try:
            status = await self._client.get_status()
        except Exception:
            status = None

        if status is None:
            from drakeling.ui.birth import BirthScreen

            self.push_screen(
                BirthScreen(self._client),
                callback=self._on_birth_dismissed,
            )
        else:
            self._push_main(status)

    def _push_main(self, status: dict) -> None:
        self.push_screen(
            MainScreen(self._client, status),
            callback=self._on_main_dismissed,
        )

    def _on_main_dismissed(self, result: object = None) -> None:
        if result == "released":
            self.run_worker(self._try_connect())

    def _on_error_dismissed(self, result: object = None) -> None:
        if result == "retry":
            self.run_worker(self._try_connect())

    def _on_birth_dismissed(self, result: object = None) -> None:
        # Result is the status dict when birth succeeded; push MainScreen
        # immediately to avoid showing a black default screen.
        if isinstance(result, dict):
            self._push_main(result)
        else:
            self.run_worker(self._show_main())

    async def _show_main(self) -> None:
        status = await self._client.get_status()
        if status:
            self._push_main(status)

    async def on_unmount(self) -> None:
        await self._client.close()


def main() -> None:
    import sys

    if "--help" in sys.argv or "-h" in sys.argv:
        print(
            "Usage: drakeling\n"
            "\n"
            "Connects to the local Drakeling daemon.\n"
            "Start the daemon first: drakelingd\n"
            "Then run: drakeling"
        )
        sys.exit(0)

    app = HatchlingApp()
    app.run()


if __name__ == "__main__":
    main()

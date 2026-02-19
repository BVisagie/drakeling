from __future__ import annotations

from typing import ClassVar

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label

from openclaw_hatchling.domain.models import DragonColour, LifecycleStage
from openclaw_hatchling.ui.client import HatchlingClient
from openclaw_hatchling.ui.widgets.feed import InteractionFeed
from openclaw_hatchling.ui.widgets.input_bar import InputBar
from openclaw_hatchling.ui.widgets.sprite_panel import SpritePanel
from openclaw_hatchling.ui.widgets.stats_display import StatsDisplay


class MainScreen(Screen):
    """Primary creature status and interaction screen."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("f2", "care_menu", "Care"),
        Binding("f3", "rest", "Rest"),
        Binding("f4", "focus_input", "Talk"),
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

    def __init__(self, client: HatchlingClient, status: dict) -> None:
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


class HatchlingApp(App):
    """Terminal UI entry point for OpenClaw Hatchling."""

    TITLE = "OpenClaw Hatchling"

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._client = HatchlingClient()

    async def on_mount(self) -> None:
        try:
            status = await self._client.get_status()
        except Exception:
            status = None

        if status is None:
            from openclaw_hatchling.ui.birth import BirthScreen

            def _on_birth_dismissed(result: object = None) -> None:
                self.run_worker(self._show_main())

            self.push_screen(BirthScreen(self._client), callback=_on_birth_dismissed)
        else:
            self.push_screen(MainScreen(self._client, status))

    async def _show_main(self) -> None:
        status = await self._client.get_status()
        if status:
            self.push_screen(MainScreen(self._client, status))

    async def on_unmount(self) -> None:
        await self._client.close()


def main() -> None:
    app = HatchlingApp()
    app.run()


if __name__ == "__main__":
    main()

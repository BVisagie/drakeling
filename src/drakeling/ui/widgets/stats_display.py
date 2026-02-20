from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static


def _bar(value: float, width: int = 12) -> str:
    filled = round(value * width)
    empty = width - filled
    if value >= 0.6:
        colour = "green"
    elif value >= 0.3:
        colour = "yellow"
    else:
        colour = "red"
    return f"[{colour}]{'█' * filled}{'░' * empty}[/] {value:.0%}"


class StatsDisplay(Static):
    """Compact stat display with coloured bars."""

    DEFAULT_CSS = """
    StatsDisplay {
        height: auto;
        padding: 0 2;
    }
    """

    def update_stats(
        self,
        mood: float,
        energy: float,
        trust: float,
        loneliness: float,
        state_curiosity: float,
        stability: float,
    ) -> None:
        # Loneliness: high is bad, invert colour logic
        loneliness_filled = round(loneliness * 12)
        loneliness_empty = 12 - loneliness_filled
        if loneliness <= 0.3:
            l_colour = "green"
        elif loneliness <= 0.6:
            l_colour = "yellow"
        else:
            l_colour = "red"
        loneliness_bar = (
            f"[{l_colour}]{'█' * loneliness_filled}{'░' * loneliness_empty}[/] "
            f"{loneliness:.0%}"
        )

        text = (
            f"  mood      {_bar(mood)}\n"
            f"  energy    {_bar(energy)}\n"
            f"  trust     {_bar(trust)}\n"
            f"  loneliness{' ' * 1}{loneliness_bar}\n"
            f"  curiosity {_bar(state_curiosity)}\n"
            f"  stability {_bar(stability)}"
        )
        self.update(text)

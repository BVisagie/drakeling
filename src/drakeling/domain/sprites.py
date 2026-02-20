"""Sprite constants for all lifecycle stages.

6 unique glyph designs, 30 named constants (one per stage per colour).
Colour tinting is applied at render time by the UI, not baked in.
"""
from __future__ import annotations

from drakeling.domain.models import DragonColour, LifecycleStage

# ---------------------------------------------------------------------------
# Base sprite designs (8-12 lines, 16-20 chars wide)
# ---------------------------------------------------------------------------

_SPRITE_EGG = r"""
      .---.
    /       \
   |  * . *  |
   | .  *  . |
   |  *   *  |
   | .  * .  |
   |  * . *  |
    \       /
      '---'
""".strip("\n")

_SPRITE_HATCHED = r"""
      .---.
    / _____ \
   | /     \ |
   |/ ^   ^ \|
    \  ._.  /
     |     |---
     | === |
      \   /
       '-'
""".strip("\n")

_SPRITE_JUVENILE = r"""
       /\
      /  \
     / ^^ \
    |  O O  |
    |  ._.  |
   /|       |\
  / |  ~~~  | \
 <  |       |  >
    |  / \  |
    | /   \ |
     /     \
""".strip("\n")

_SPRITE_MATURE = r"""
        /\    /\
       /  \  /  \
      / ^^ \/ ^^ \
     |    O  O    |
     |    .__.    |
    /|            |\
   / |   ~~~~~~   | \
  <  |            |  >
   \ |    /  \    | /
    \|   /    \   |/
     |  /      \  |
      \/        \/
""".strip("\n")

_SPRITE_RESTING = r"""
           __
    /\    /  }
   /  \--/  /
  / ^^ __ \/
 |  - -   |
  \ .__.  \
   \~~~~~~ \
    \       }
     \  ~  /
      '---'
""".strip("\n")

_SPRITE_EXHAUSTED = r"""
        /\    /\
       /  \  /  \
      / -- \/ -- \
     |    -  -    |
     |    .__.    |
    /|            |\
   v |   ......   | v
     |            |
     |    /  \    |
      \  /    \  /
       \/      \/
""".strip("\n")

# ---------------------------------------------------------------------------
# 30 named constants (one per stage x colour), aliasing the 6 base designs.
# Per-colour artwork variants can be added later by replacing the alias.
# ---------------------------------------------------------------------------

SPRITE_EGG_RED = _SPRITE_EGG
SPRITE_EGG_GREEN = _SPRITE_EGG
SPRITE_EGG_BLUE = _SPRITE_EGG
SPRITE_EGG_WHITE = _SPRITE_EGG
SPRITE_EGG_GOLD = _SPRITE_EGG

SPRITE_HATCHED_RED = _SPRITE_HATCHED
SPRITE_HATCHED_GREEN = _SPRITE_HATCHED
SPRITE_HATCHED_BLUE = _SPRITE_HATCHED
SPRITE_HATCHED_WHITE = _SPRITE_HATCHED
SPRITE_HATCHED_GOLD = _SPRITE_HATCHED

SPRITE_JUVENILE_RED = _SPRITE_JUVENILE
SPRITE_JUVENILE_GREEN = _SPRITE_JUVENILE
SPRITE_JUVENILE_BLUE = _SPRITE_JUVENILE
SPRITE_JUVENILE_WHITE = _SPRITE_JUVENILE
SPRITE_JUVENILE_GOLD = _SPRITE_JUVENILE

SPRITE_MATURE_RED = _SPRITE_MATURE
SPRITE_MATURE_GREEN = _SPRITE_MATURE
SPRITE_MATURE_BLUE = _SPRITE_MATURE
SPRITE_MATURE_WHITE = _SPRITE_MATURE
SPRITE_MATURE_GOLD = _SPRITE_MATURE

SPRITE_RESTING_RED = _SPRITE_RESTING
SPRITE_RESTING_GREEN = _SPRITE_RESTING
SPRITE_RESTING_BLUE = _SPRITE_RESTING
SPRITE_RESTING_WHITE = _SPRITE_RESTING
SPRITE_RESTING_GOLD = _SPRITE_RESTING

SPRITE_EXHAUSTED_RED = _SPRITE_EXHAUSTED
SPRITE_EXHAUSTED_GREEN = _SPRITE_EXHAUSTED
SPRITE_EXHAUSTED_BLUE = _SPRITE_EXHAUSTED
SPRITE_EXHAUSTED_WHITE = _SPRITE_EXHAUSTED
SPRITE_EXHAUSTED_GOLD = _SPRITE_EXHAUSTED

# ---------------------------------------------------------------------------
# Lookup table and accessor
# ---------------------------------------------------------------------------

_SPRITE_MAP: dict[tuple[LifecycleStage, DragonColour], str] = {
    (LifecycleStage.EGG, DragonColour.RED): SPRITE_EGG_RED,
    (LifecycleStage.EGG, DragonColour.GREEN): SPRITE_EGG_GREEN,
    (LifecycleStage.EGG, DragonColour.BLUE): SPRITE_EGG_BLUE,
    (LifecycleStage.EGG, DragonColour.WHITE): SPRITE_EGG_WHITE,
    (LifecycleStage.EGG, DragonColour.GOLD): SPRITE_EGG_GOLD,
    (LifecycleStage.HATCHED, DragonColour.RED): SPRITE_HATCHED_RED,
    (LifecycleStage.HATCHED, DragonColour.GREEN): SPRITE_HATCHED_GREEN,
    (LifecycleStage.HATCHED, DragonColour.BLUE): SPRITE_HATCHED_BLUE,
    (LifecycleStage.HATCHED, DragonColour.WHITE): SPRITE_HATCHED_WHITE,
    (LifecycleStage.HATCHED, DragonColour.GOLD): SPRITE_HATCHED_GOLD,
    (LifecycleStage.JUVENILE, DragonColour.RED): SPRITE_JUVENILE_RED,
    (LifecycleStage.JUVENILE, DragonColour.GREEN): SPRITE_JUVENILE_GREEN,
    (LifecycleStage.JUVENILE, DragonColour.BLUE): SPRITE_JUVENILE_BLUE,
    (LifecycleStage.JUVENILE, DragonColour.WHITE): SPRITE_JUVENILE_WHITE,
    (LifecycleStage.JUVENILE, DragonColour.GOLD): SPRITE_JUVENILE_GOLD,
    (LifecycleStage.MATURE, DragonColour.RED): SPRITE_MATURE_RED,
    (LifecycleStage.MATURE, DragonColour.GREEN): SPRITE_MATURE_GREEN,
    (LifecycleStage.MATURE, DragonColour.BLUE): SPRITE_MATURE_BLUE,
    (LifecycleStage.MATURE, DragonColour.WHITE): SPRITE_MATURE_WHITE,
    (LifecycleStage.MATURE, DragonColour.GOLD): SPRITE_MATURE_GOLD,
    (LifecycleStage.RESTING, DragonColour.RED): SPRITE_RESTING_RED,
    (LifecycleStage.RESTING, DragonColour.GREEN): SPRITE_RESTING_GREEN,
    (LifecycleStage.RESTING, DragonColour.BLUE): SPRITE_RESTING_BLUE,
    (LifecycleStage.RESTING, DragonColour.WHITE): SPRITE_RESTING_WHITE,
    (LifecycleStage.RESTING, DragonColour.GOLD): SPRITE_RESTING_GOLD,
    (LifecycleStage.EXHAUSTED, DragonColour.RED): SPRITE_EXHAUSTED_RED,
    (LifecycleStage.EXHAUSTED, DragonColour.GREEN): SPRITE_EXHAUSTED_GREEN,
    (LifecycleStage.EXHAUSTED, DragonColour.BLUE): SPRITE_EXHAUSTED_BLUE,
    (LifecycleStage.EXHAUSTED, DragonColour.WHITE): SPRITE_EXHAUSTED_WHITE,
    (LifecycleStage.EXHAUSTED, DragonColour.GOLD): SPRITE_EXHAUSTED_GOLD,
}


def get_sprite(stage: LifecycleStage, colour: DragonColour) -> str:
    """Return the sprite art for a given lifecycle stage and colour."""
    return _SPRITE_MAP[(stage, colour)]

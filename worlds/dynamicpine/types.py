from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from worlds.AutoWorld import World

    from .api import DynamicPineGame

type LauncherOptions = Literal["simple", "full", "client", "patch"]

# PCSX2.ini settings as {section: {key: value}}
type Overrides = dict[str, dict[str, str]]

# A World class, a game name, a PS2 serial, or a DynamicPineGame
type WorldOrGame = type[World] | str | DynamicPineGame

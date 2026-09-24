"""Shared type aliases for Dynamic Pine's public dataclass fields and function
signatures. Kept in one leaf module (no runtime imports of its own besides
typing) so api.py, config.py, and launcher.py can all import from it without
circular imports - api.py already imports from config.py, so config.py can't
import anything back from api.py, and launcher.py imports from api.py."""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from worlds.AutoWorld import World

    from .api import DynamicPineGame

type LauncherOptions = Literal["simple", "full", "client", "patch"]
"""DynamicPineGame.launcher_options - see its docstring in api.py."""

type Overrides = dict[str, dict[str, str]]
"""A set of PCSX2.ini settings as {section: {key: value}} - the shape of both
DynamicPineGame.ini_overrides and config.py's BASE_INI_SETTINGS."""

type WorldOrGame = type[World] | str | DynamicPineGame
"""Anything resolve_game (and everything that calls it: get_pine_port,
ensure_instance_config, launch_pcsx2) accepts to identify a game: a World
class, a game name, a PS2 serial, or a DynamicPineGame directly."""

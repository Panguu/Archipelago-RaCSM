"""Consumer-facing API for Dynamic Pine.

A game world opts in by setting a class attribute on its World:

    from worlds.dynamicpine import DynamicPineGame

    class MyPS2World(World):
        dynamic_pine = DynamicPineGame(
            game_id="SCUS-97615",
            client_component="My Game Client",
        )

and its client asks Dynamic Pine for the PINE port to use (typically from its
"Connected" package handler, once the slot name is known):

    from worlds.dynamicpine import launch_pcsx2
    port = launch_pcsx2("My Game", slot_name)

Dynamic Pine handles everything else: the per-instance portable PCSX2 ini
(PINE enabled on a free port, its own memcard, shared BIOS folder,
RetroAchievements disabled), and launching PCSX2 with the ISO the user
configured under dynamic_pine_options.game_files in host.yaml.
"""
from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from worlds.AutoWorld import World

# Set once, in the hub client's own process, before it does anything else (see
# client.run_client) - inherited by any game client it later spawns via
# launch_game_client, since multiprocessing.Process children inherit the
# parent's environment at spawn time. Lets launch_pcsx2 refuse to do
# anything for a game client started any other way (double-clicked from the AP
# Launcher, run directly from a shell, etc.), per the "Dynamic Pine should only
# ever be active when launched through the Dynamic Pine hub" requirement.
_LAUNCHED_VIA_HUB_ENV_VAR = "ARCHIPELAGO_DYNAMIC_PINE_HUB"

# Set by launch_pcsx2 (in the hub process) every time it resolves a
# port for an instance - inherited by any game client the hub spawns
# afterwards (see _LAUNCHED_VIA_HUB_ENV_VAR above for why that inheritance
# works). One client process only ever needs its own instance's port, so a
# single fixed name is enough - no per-game keying.
#
# This is a fast-path only: a client should still call launch_pcsx2
# itself once it knows its slot name (e.g. in its Connected handler) as the
# source of truth. That call is what actually launches PCSX2 if it isn't
# running yet, and it's what re-resolves the port if this instance's PCSX2
# wasn't already running when the hub spawned the client (so the env var
# hadn't been set yet, or was stale). Reading the env var first just lets a
# client point its Pine connection at an already-running instance immediately
# on startup instead of waiting for that round trip.
_PINE_PORT_ENV_VAR = "ARCHIPELAGO_DYNAMIC_PINE_PORT"


def launched_via_hub() -> bool:
    """True if this process is the Dynamic Pine hub client itself, or a game
    client the hub spawned (directly or transitively) - see
    _LAUNCHED_VIA_HUB_ENV_VAR above for how that's tracked across processes."""
    return os.environ.get(_LAUNCHED_VIA_HUB_ENV_VAR) == "1"


def mark_launched_via_hub() -> None:
    """Called once by the hub client's own startup - see _LAUNCHED_VIA_HUB_ENV_VAR."""
    os.environ[_LAUNCHED_VIA_HUB_ENV_VAR] = "1"


def mark_pine_port(port: int) -> None:
    """Called by launch_pcsx2 (hub process) every time it resolves a
    port for an instance - see _PINE_PORT_ENV_VAR."""
    os.environ[_PINE_PORT_ENV_VAR] = str(port)


def get_pine_port_from_env() -> int | None:
    """The port set by the most recent launch_pcsx2 call in this
    process (or an ancestor process, e.g. the hub) - None if not set. See
    _PINE_PORT_ENV_VAR for why this is a fast-path, not a replacement for
    calling launch_pcsx2."""
    raw = os.environ.get(_PINE_PORT_ENV_VAR)
    try:
        return int(raw) if raw else None
    except ValueError:
        return None


@dataclasses.dataclass
class DynamicPineGame:
    """Declares Dynamic Pine support for one PS2 game world.

    Set as a `dynamic_pine` class attribute on the game's World subclass -
    Dynamic Pine discovers supported games by scanning the world registry for
    this attribute, so a consumer needs no Dynamic Pine imports beyond this
    dataclass (and should guard even that with try/except ImportError, since
    Dynamic Pine is a separately-installed apworld)."""

    game_id: str
    """The game's PS2 serial as PCSX2/PINE reports it, e.g. "SCUS-97615". Also
    the key users put under dynamic_pine_options.game_files in host.yaml, and
    the folder name instances are grouped under inside the PCSX2 data root."""

    client_component: str | None = None
    """display_name of the game's client Component in the AP Launcher, used by
    the Dynamic Pine hub client's "Launch Client" button. None hides that
    button (PCSX2 launching still works)."""

    memcard_name: str = "memcard.ps2"
    """Per-instance memcard filename written into each instance's ini."""

    ini_overrides: dict[str, dict[str, str]] = dataclasses.field(default_factory=dict)
    """Extra PCSX2.ini settings this game needs, as {section: {key: value}},
    merged on top of Dynamic Pine's base settings each time an instance's ini
    is (re)built."""


def discover_games() -> "dict[str, tuple[type[World], DynamicPineGame]]":
    """All installed worlds that declare Dynamic Pine support, as
    {game name: (world class, its DynamicPineGame declaration)}."""
    from worlds.AutoWorld import AutoWorldRegister

    found: "dict[str, tuple[type[World], DynamicPineGame]]" = {}
    for game_name, world_type in AutoWorldRegister.world_types.items():
        spec = getattr(world_type, "dynamic_pine", None)
        if isinstance(spec, DynamicPineGame):
            found[game_name] = (world_type, spec)
    return found


def resolve_game(world_or_game: "type[World] | str | DynamicPineGame") -> tuple[str, DynamicPineGame]:
    """Accepts a World class, a game name, a PS2 serial, or a DynamicPineGame
    directly, and returns (display name, spec). Raises ValueError for
    unknown/unsupported games."""
    if isinstance(world_or_game, DynamicPineGame):
        # Look the display name back up so log messages stay readable.
        for game_name, (_, spec) in discover_games().items():
            if spec is world_or_game:
                return game_name, spec
        return world_or_game.game_id, world_or_game
    if isinstance(world_or_game, str):
        games = discover_games()
        if world_or_game in games:
            return world_or_game, games[world_or_game][1]
        for game_name, (_, spec) in games.items():
            if spec.game_id == world_or_game:
                return game_name, spec
        raise ValueError(f"{world_or_game!r} is not an installed Dynamic Pine game")
    spec = getattr(world_or_game, "dynamic_pine", None)
    if not isinstance(spec, DynamicPineGame):
        raise ValueError(f"{world_or_game!r} does not declare a dynamic_pine attribute")
    return getattr(world_or_game, "game", world_or_game.__name__), spec


def dynamic_pine_settings():
    """The dynamic_pine_options settings group from host.yaml
    (see DynamicPineSettings in __init__.py)."""
    from . import DynamicPineWorld
    return DynamicPineWorld.settings


def get_iso_path(spec: DynamicPineGame) -> Path | None:
    """The user's configured ISO for this game from
    dynamic_pine_options.game_files, or None if they haven't set one."""
    game_files = dict(dynamic_pine_settings().game_files or {})
    raw = game_files.get(spec.game_id)
    return Path(str(raw)).expanduser() if raw else None


def set_iso_path(spec: DynamicPineGame, iso_path: str) -> None:
    """Records the user's ISO for this game under
    dynamic_pine_options.game_files and persists it to host.yaml, so they're
    only ever asked to locate a game once."""
    from settings import get_settings

    group = dynamic_pine_settings()
    game_files = dict(group.game_files or {})
    game_files[spec.game_id] = iso_path
    group.game_files = game_files
    get_settings().save()


def get_bios_path() -> Path | None:
    """The user's configured shared BIOS folder from
    dynamic_pine_options.bios_path, or None if they haven't set one."""
    raw = dynamic_pine_settings().bios_path
    return Path(str(raw)).expanduser() if raw else None


def set_bios_path(bios_path: str) -> None:
    """Records the user's shared BIOS folder under dynamic_pine_options.bios_path
    and persists it to host.yaml - applies to every game/instance Dynamic Pine
    launches, so this only ever needs setting once."""
    from settings import get_settings

    dynamic_pine_settings().bios_path = bios_path
    get_settings().save()


def get_pine_port(world_or_game: "type[World] | str | DynamicPineGame",
                  slot_name: str | None = None) -> int | None:
    """The PINE port recorded in this game instance's ini, or None if the
    instance has never been configured. Purely a lookup - doesn't build configs
    or launch anything; use launch_pcsx2 for that."""
    from .config import DynamicPineConfig
    from .launcher import instance_id_for

    _, spec = resolve_game(world_or_game)
    data_root = Path(dynamic_pine_settings().pcsx2_data_path.resolve())
    _, config_path = DynamicPineConfig.paths_for(data_root, spec.game_id, instance_id_for(slot_name))
    if not config_path.exists():
        return None
    return DynamicPineConfig.read_existing_port(config_path)

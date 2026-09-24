"""Consumer-facing API for Dynamic Pine: DynamicPineGame plus every function a
game world or its client calls into. See docs/adding_to_apworld.md for the
full integration guide and docs/api.md for the reference."""
from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import TYPE_CHECKING

from settings import get_settings

from .config import DynamicPineConfig
from .types import LauncherOptions, Overrides, WorldOrGame

if TYPE_CHECKING:
    from worlds.AutoWorld import World

_LAUNCHED_VIA_HUB_ENV_VAR = "ARCHIPELAGO_DYNAMIC_PINE_HUB"
_PINE_PORT_ENV_VAR = "ARCHIPELAGO_DYNAMIC_PINE_PORT"
_PCSX2_ALREADY_LAUNCHED_ENV_VAR = "ARCHIPELAGO_DYNAMIC_PINE_PCSX2_LAUNCHED"
_AUTH_ENV_VAR = "ARCHIPELAGO_DYNAMIC_PINE_AUTH"


def launched_via_hub() -> bool:
    """True if this process is the Dynamic Pine hub, or a client it spawned."""
    return os.environ.get(_LAUNCHED_VIA_HUB_ENV_VAR) == "1"


def mark_launched_via_hub() -> None:
    """Marks this process as launched_via_hub() - called by the hub client's
    own startup, and by any client that self-launches PCSX2 (see docs)."""
    os.environ[_LAUNCHED_VIA_HUB_ENV_VAR] = "1"


def mark_pine_port(port: int) -> None:
    """Records the port launch_pcsx2 just resolved, for get_pine_port_from_env()."""
    os.environ[_PINE_PORT_ENV_VAR] = str(port)


def get_pine_port_from_env() -> int | None:
    """The port set by the most recent launch_pcsx2/ensure_instance_config
    call in this process or an ancestor (e.g. the hub) - None if unset. A
    fast-path only, not a replacement for calling launch_pcsx2."""
    raw = os.environ.get(_PINE_PORT_ENV_VAR)
    try:
        return int(raw) if raw else None
    except ValueError:
        return None


def mark_pending_auth(slot_name: str) -> None:
    """Records the slot name the hub launched this client's instance under
    (its "instance" argument to /launch, which by convention must already
    match the slot the player will connect with - see get_pine_port), so
    the about-to-be-spawned client can pre-fill its own auth with it
    instead of prompting the player to type the same name again."""
    os.environ[_AUTH_ENV_VAR] = slot_name


def get_pending_auth() -> str | None:
    """The slot name mark_pending_auth() recorded for this launch, or None
    if the hub wasn't given one (e.g. "instance" left as the "default"
    default). A fast-path read only - doesn't validate the name is actually
    correct for the seed being connected to."""
    return os.environ.get(_AUTH_ENV_VAR) or None


def mark_pcsx2_already_launched() -> None:
    """Marks that this launch already handled PCSX2 - set by the hub's
    "simple" launcher_options button right before it spawns the client."""
    os.environ[_PCSX2_ALREADY_LAUNCHED_ENV_VAR] = "1"


def pcsx2_already_launched_via_env() -> bool:
    """True if PCSX2 was already launched for this instance as part of the
    same "simple" launch action - skip calling launch_pcsx2 and just resolve
    the port. Not a guarantee that PCSX2 is still running."""
    return os.environ.get(_PCSX2_ALREADY_LAUNCHED_ENV_VAR) == "1"


@dataclasses.dataclass
class DynamicPineGame:
    """Declares Dynamic Pine support for one PS2 game world. Set as a
    `dynamic_pine` class attribute on the World subclass - guard the import
    with try/except ImportError, since Dynamic Pine is a separate apworld.
    See docs/adding_to_apworld.md for the full guide."""

    game_ids: str | tuple[str, ...]
    """This game's PS2 serial(s), e.g. "SCUS-97615" - pass a tuple to accept
    multiple releases (regions, a patched re-release). Normalized to a tuple
    in __post_init__; game_ids[0] is the canonical one Dynamic Pine organizes
    data and new game_files entries under."""

    client_component: str | None = None
    """display_name of the game's client Component in the AP Launcher, used by
    the hub's "Launch Client" button. None hides that button."""

    memcard_name: str = "memcard.ps2"
    """Per-instance memcard filename written into each instance's ini."""

    ini_overrides: Overrides = dataclasses.field(default_factory=dict)
    """Extra PCSX2.ini settings this game needs, as {section: {key: value}} -
    see docs/ini_settings.md."""

    launcher_options: LauncherOptions = "full"
    """Controls the hub's per-game button layout - see docs/adding_to_apworld.md
    for what each of "full" (default), "simple", "client", and "patch" do."""

    patch_file_suffix: str | None = None
    """File extension (e.g. ".aprac2"), with the leading dot, of this game's
    per-seed patch file. Only meaningful with launcher_options="patch"."""

    def __post_init__(self) -> None:
        if isinstance(self.game_ids, str):
            self.game_ids = (self.game_ids,)
        else:
            self.game_ids = tuple(self.game_ids)
        if not self.game_ids:
            raise ValueError("DynamicPineGame needs at least one game id")


def discover_games() -> dict[str, tuple[type[World], DynamicPineGame]]:
    """All installed worlds that declare Dynamic Pine support, as
    {game name: (world class, its DynamicPineGame declaration)}."""
    from worlds.AutoWorld import AutoWorldRegister

    found: dict[str, tuple[type[World], DynamicPineGame]] = {}
    for game_name, world_type in AutoWorldRegister.world_types.items():
        spec = getattr(world_type, "dynamic_pine", None)
        if isinstance(spec, DynamicPineGame):
            found[game_name] = (world_type, spec)
    return found


def resolve_game(world_or_game: WorldOrGame) -> tuple[str, DynamicPineGame]:
    """Accepts a World class, a game name, a PS2 serial, or a DynamicPineGame
    directly, and returns (display name, spec). Raises ValueError for
    unknown/unsupported games."""
    if isinstance(world_or_game, DynamicPineGame):
        # Look the display name back up so log messages stay readable.
        for game_name, (_, spec) in discover_games().items():
            if spec is world_or_game:
                return game_name, spec
        return world_or_game.game_ids[0], world_or_game
    if isinstance(world_or_game, str):
        games = discover_games()
        if world_or_game in games:
            return world_or_game, games[world_or_game][1]
        for game_name, (_, spec) in games.items():
            if world_or_game in spec.game_ids:
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
    dynamic_pine_options.game_files, or None if they haven't set one under any
    of the game's accepted serials (spec.game_ids)."""
    game_files = dict(dynamic_pine_settings().game_files or {})
    for game_id in spec.game_ids:
        raw = game_files.get(game_id)
        if raw:
            return Path(str(raw)).expanduser()
    return None


def set_iso_path(spec: DynamicPineGame, iso_path: str) -> None:
    """Records the user's ISO under dynamic_pine_options.game_files and
    persists it to host.yaml. Written under whichever accepted serial already
    has an entry, else the canonical spec.game_ids[0]."""
    group = dynamic_pine_settings()
    game_files = dict(group.game_files or {})
    key = next((game_id for game_id in spec.game_ids if game_id in game_files), spec.game_ids[0])
    game_files[key] = iso_path
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
    dynamic_pine_settings().bios_path = bios_path
    get_settings().save()


def get_pine_port(world_or_game: WorldOrGame,
                  slot_name: str | None = None) -> int | None:
    """The PINE port recorded in this game instance's ini, or None if the
    instance has never been configured. Purely a lookup - doesn't build configs
    or launch anything; use launch_pcsx2 for that."""
    from .launcher import instance_id_for

    _, spec = resolve_game(world_or_game)
    data_root = Path(dynamic_pine_settings().pcsx2_data_path.resolve())
    _, config_path = DynamicPineConfig.paths_for(data_root, spec.game_ids[0], instance_id_for(slot_name))
    if not config_path.exists():
        return None
    return DynamicPineConfig.read_existing_port(config_path)

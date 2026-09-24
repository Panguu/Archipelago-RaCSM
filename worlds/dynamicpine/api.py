import dataclasses
import os
import re
from pathlib import Path

from settings import get_settings
from Utils import user_path
from worlds.AutoWorld import AutoWorldRegister, World

from .config import DynamicPineConfig
from .types import LauncherOptions, Overrides, WorldOrGame
from .world import DynamicPineWorld

_LAUNCHED_VIA_HUB_ENV_VAR = "ARCHIPELAGO_DYNAMIC_PINE_HUB"
_PINE_PORT_ENV_VAR = "ARCHIPELAGO_DYNAMIC_PINE_PORT"
_PCSX2_ALREADY_LAUNCHED_ENV_VAR = "ARCHIPELAGO_DYNAMIC_PINE_PCSX2_LAUNCHED"
_AUTH_ENV_VAR = "ARCHIPELAGO_DYNAMIC_PINE_AUTH"
_UNSAFE_PATH_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def launched_via_hub() -> bool:
    return os.environ.get(_LAUNCHED_VIA_HUB_ENV_VAR) == "1"


def mark_launched_via_hub() -> None:
    os.environ[_LAUNCHED_VIA_HUB_ENV_VAR] = "1"


def mark_pine_port(port: int) -> None:
    os.environ[_PINE_PORT_ENV_VAR] = str(port)


def get_pine_port_from_env() -> int | None:
    raw = os.environ.get(_PINE_PORT_ENV_VAR)
    try:
        return int(raw) if raw else None
    except ValueError:
        return None


def mark_pending_auth(slot_name: str) -> None:
    os.environ[_AUTH_ENV_VAR] = slot_name


def get_pending_auth() -> str | None:
    return os.environ.get(_AUTH_ENV_VAR) or None


def mark_pcsx2_already_launched() -> None:
    os.environ[_PCSX2_ALREADY_LAUNCHED_ENV_VAR] = "1"


def pcsx2_already_launched_via_env() -> bool:
    return os.environ.get(_PCSX2_ALREADY_LAUNCHED_ENV_VAR) == "1"


def instance_id_for(slot_name: str | None) -> str:
    if not slot_name:
        return "default"
    return _UNSAFE_PATH_CHARS.sub("_", slot_name).strip(" .") or "default"


@dataclasses.dataclass
class DynamicPineGame:
    # game_ids[0] is the canonical serial that data and new game_files entries go under
    game_ids: str | tuple[str, ...]
    client_component: str | None = None
    memcard_name: str = "memcard.ps2"
    ini_overrides: Overrides = dataclasses.field(default_factory=dict)
    launcher_options: LauncherOptions = "full"
    patch_file_suffix: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.game_ids, str):
            self.game_ids = (self.game_ids,)
        else:
            self.game_ids = tuple(self.game_ids)
        if not self.game_ids:
            raise ValueError("DynamicPineGame needs at least one game id")


def discover_games() -> dict[str, tuple[type[World], DynamicPineGame]]:
    found: dict[str, tuple[type[World], DynamicPineGame]] = {}
    for game_name, world_type in AutoWorldRegister.world_types.items():
        spec = getattr(world_type, "dynamic_pine", None)
        if isinstance(spec, DynamicPineGame):
            found[game_name] = (world_type, spec)
    return found


def resolve_game(world_or_game: WorldOrGame) -> tuple[str, DynamicPineGame]:
    if isinstance(world_or_game, DynamicPineGame):
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
    return DynamicPineWorld.settings


def _named_isos(raw: object, game_id: str) -> dict[str, str]:
    # Old configs store one plain path per serial; treat it as a single ISO named after the serial
    if isinstance(raw, dict):
        return {str(name): str(path) for name, path in raw.items() if path}
    return {game_id: str(raw)} if raw else {}


def get_iso_options(spec: DynamicPineGame) -> dict[str, Path]:
    game_files = dynamic_pine_settings().game_files or {}
    options: dict[str, Path] = {}
    for game_id in spec.game_ids:
        for name, path in _named_isos(game_files.get(game_id), game_id).items():
            options.setdefault(name, Path(path).expanduser())
    return options


def get_selected_iso_name(spec: DynamicPineGame) -> str | None:
    options = get_iso_options(spec)
    selected = (dynamic_pine_settings().selected_isos or {}).get(spec.game_ids[0])
    return selected if selected in options else next(iter(options), None)


def get_iso_path(spec: DynamicPineGame) -> Path | None:
    name = get_selected_iso_name(spec)
    return get_iso_options(spec)[name] if name is not None else None


def set_selected_iso(spec: DynamicPineGame, name: str) -> None:
    group = dynamic_pine_settings()
    group.selected_isos = {**(group.selected_isos or {}), spec.game_ids[0]: name}
    get_settings().save()


def set_iso_path(spec: DynamicPineGame, iso_path: str, name: str | None = None) -> str:
    group = dynamic_pine_settings()
    game_files = dict(group.game_files or {})
    key = spec.game_ids[0]
    name = name or Path(iso_path).stem
    game_files[key] = {**_named_isos(game_files.get(key), key), name: iso_path}
    group.game_files = game_files
    set_selected_iso(spec, name)
    return name


def remove_iso(spec: DynamicPineGame, name: str) -> bool:
    group = dynamic_pine_settings()
    game_files = dict(group.game_files or {})
    for game_id in spec.game_ids:
        entries = _named_isos(game_files.get(game_id), game_id)
        if name in entries:
            del entries[name]
            if entries:
                game_files[game_id] = entries
            else:
                del game_files[game_id]
            group.game_files = game_files
            get_settings().save()
            return True
    return False


def get_bios_path() -> Path | None:
    raw = dynamic_pine_settings().bios_path
    # set_bios_path stores a plain str until host.yaml is reloaded
    path = Path(raw.resolve() if hasattr(raw, "resolve") else raw) if raw else None
    # Archipelago turns an empty folder setting into its own install folder, so treat that as unset
    if path is None or path == Path(user_path()):
        return None
    return path


def set_bios_path(bios_path: str) -> None:
    dynamic_pine_settings().bios_path = bios_path
    get_settings().save()


def get_pine_port(world_or_game: WorldOrGame,
                  slot_name: str | None = None) -> int | None:
    _, spec = resolve_game(world_or_game)
    data_root = Path(dynamic_pine_settings().pcsx2_data_path.resolve())
    _, config_path = DynamicPineConfig.paths_for(data_root, spec.game_ids[0], instance_id_for(slot_name))
    if not config_path.exists():
        return None
    return DynamicPineConfig.read_existing_port(config_path)

"""Dynamic Pine - shared PCSX2/PINE infrastructure for Archipelago PS2 game
worlds. Copied into the worlds/ folder like Universal Tracker.

Game worlds opt in with a single class attribute (see api.DynamicPineGame);
Dynamic Pine then owns everything PCSX2: per-instance portable inis with PINE
enabled on a free port, per-instance memcards, a shared BIOS folder,
RetroAchievements disabled, launching PCSX2 with the user's ISO from host.yaml,
and a hub client with a tab per supported game for launching emulator instances
and the games' own (unmodified) clients."""
from typing import ClassVar, Union

from settings import Group, OptionalUserFolderPath, UserFilePath, UserFolderPath
from worlds.AutoWorld import World
from worlds.LauncherComponents import Component, Type, components

from .api import (DynamicPineGame, discover_games, dynamic_pine_settings, get_bios_path,
                  get_iso_path, get_pine_port, get_pine_port_from_env, launched_via_hub,
                  resolve_game, set_bios_path, set_iso_path)
from .launcher import (InstanceAlreadyRunningError, clear_unused_instances, ensure_instance_config,
                       launch_pcsx2, list_instances, list_running_instances, prompt_for_bios,
                       prompt_for_iso, remove_instance)

DYNAMIC_PINE_VERSION = "v0.1.0"

__all__ = [
    "DYNAMIC_PINE_VERSION", "DynamicPineGame", "DynamicPineSettings", "DynamicPineWorld",
    "InstanceAlreadyRunningError", "clear_unused_instances", "discover_games", "dynamic_pine_settings",
    "ensure_instance_config", "get_bios_path", "get_iso_path", "get_pine_port", "get_pine_port_from_env",
    "launch_pcsx2", "launched_via_hub", "list_instances", "list_running_instances", "prompt_for_bios",
    "prompt_for_iso", "remove_instance", "resolve_game", "set_bios_path", "set_iso_path",
]


def launch_client(*args) -> None:
    from worlds.LauncherComponents import launch
    from .client import run_client
    launch(run_client, name="Dynamic Pine client", args=args)


class DynamicPineSettings(Group):
    class Pcsx2Path(UserFilePath):
        """Path to your PCSX2 executable, shared by every Dynamic Pine game.
        Used to launch the emulator automatically with PINE enabled. If this
        file can't be found, you'll be prompted to browse for it (and the
        choice is remembered)."""
        description = "PCSX2 Executable"
        is_exe = True

    class Pcsx2DataPath(UserFolderPath):
        """Root folder Dynamic Pine uses for PCSX2's portable settings data. A
        subfolder named after each game's serial (e.g. SCUS-97615) and then the
        connecting slot name is created per running instance, each with its own
        PINE-enabled PCSX2.ini, port, and memcard - kept separate from your
        regular PCSX2 install/settings, and from each other, so multiple games
        and slots can run at once."""
        description = "Dynamic Pine PCSX2 Data Directory"

    class BiosPath(OptionalUserFolderPath):
        """Folder containing your PCSX2 BIOS file(s). Shared across every PCSX2
        instance Dynamic Pine launches, so you only complete PCSX2's BIOS setup
        once instead of once per game/instance. Leave unset to let each new
        instance prompt for its own BIOS the first time it's created."""
        description = "PCSX2 BIOS Directory"

    class GameFiles(dict):
        """Paths to your own copies of each supported game's ISO, keyed by the
        game's PS2 serial. Format is:
          SCUS-97615: C:/isos/Ratchet and Clank Size Matters.iso
        with each game on its own line and indented two spaces. A game with no
        entry here can still be played - Dynamic Pine just won't be able to
        launch PCSX2 for it automatically."""

    pcsx2_path: Union[Pcsx2Path, str] = Pcsx2Path("pcsx2.exe")
    pcsx2_data_path: Union[Pcsx2DataPath, str] = Pcsx2DataPath("dynamic_pine_pcsx2_data")
    bios_path: Union[BiosPath, str] = BiosPath("")
    game_files: Union[GameFiles, dict] = {}


class DynamicPineWorld(World):
    """Not a playable game - registers Dynamic Pine's shared host.yaml settings,
    the same trick Universal Tracker's TrackerWorld uses."""
    settings: ClassVar[DynamicPineSettings]
    settings_key = "dynamic_pine_options"

    # to make auto world register happy so we can register our settings
    game = "Dynamic Pine"
    hidden = True
    item_name_to_id = {}
    location_name_to_id = {}


components.append(Component("Dynamic Pine", None, func=launch_client, component_type=Type.CLIENT))

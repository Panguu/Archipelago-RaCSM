"""Dynamic Pine - shared PCSX2/PINE infrastructure for Archipelago PS2 game
worlds. Copied into the worlds/ folder like Universal Tracker.

Game worlds opt in with a single class attribute (see api.DynamicPineGame);
Dynamic Pine then owns everything PCSX2: per-instance portable inis with PINE
enabled on a free port, per-instance memcards, a shared BIOS folder,
RetroAchievements disabled, launching PCSX2 with the user's ISO from host.yaml,
and a hub client with a tab per supported game for launching emulator instances
and the games' own (unmodified) clients."""
from .api import (DynamicPineGame, discover_games, dynamic_pine_settings, get_bios_path,
                  get_iso_path, get_pine_port, get_pine_port_from_env, launched_via_hub,
                  mark_launched_via_hub, mark_pcsx2_already_launched, pcsx2_already_launched_via_env,
                  resolve_game, set_bios_path, set_iso_path)
from .command_mixin import DynamicPineCommandMixin
from .launcher import (InstanceAlreadyRunningError, NoBiosConfigured, NoIsoConfigured, NoPCSX2Executable,
                       clear_unused_instances, ensure_instance_config, launch_pcsx2, list_instances,
                       list_running_instances, prompt_for_bios, prompt_for_iso, remove_instance)
from .options import DynamicPineSettings
from .world import DYNAMIC_PINE_VERSION, DynamicPineWorld

__all__ = [
    "DYNAMIC_PINE_VERSION", "DynamicPineCommandMixin", "DynamicPineGame", "DynamicPineSettings",
    "DynamicPineWorld", "InstanceAlreadyRunningError", "NoBiosConfigured", "NoIsoConfigured",
    "NoPCSX2Executable", "clear_unused_instances", "discover_games", "dynamic_pine_settings",
    "ensure_instance_config", "get_bios_path", "get_iso_path", "get_pine_port", "get_pine_port_from_env",
    "launch_pcsx2", "launched_via_hub", "list_instances", "list_running_instances",
    "mark_launched_via_hub", "mark_pcsx2_already_launched", "pcsx2_already_launched_via_env",
    "prompt_for_bios", "prompt_for_iso", "remove_instance", "resolve_game", "set_bios_path", "set_iso_path",
]

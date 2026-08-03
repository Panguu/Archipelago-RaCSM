"""Builds per-instance PINE-enabled PCSX2 configs and launches PCSX2 for any
Dynamic Pine game, driven by the shared dynamic_pine_options host.yaml settings
(see DynamicPineSettings in __init__.py). Generalized from
rac_size_matters/client/launcher.py."""
from __future__ import annotations

import dataclasses
import logging
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from .api import (DynamicPineGame, dynamic_pine_settings, get_iso_path, launched_via_hub,
                  mark_pine_port, resolve_game, set_bios_path, set_iso_path)
from .config import DynamicPineConfig

if TYPE_CHECKING:
    from worlds.AutoWorld import World

_UNSAFE_PATH_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_PID_FILENAME = "dynamicpine_pcsx2.pid"


class InstanceAlreadyRunningError(RuntimeError):
    """Raised by launch_pcsx2 when the target game+slot instance already has a
    live Dynamic-Pine-launched PCSX2 process - callers should surface this to
    the user rather than silently reusing or relaunching it."""

# CommonClient's logger, referenced by name so this module never imports
# CommonClient - launcher.py gets imported during world registration (via
# worlds/dynamicpine/__init__.py), and CommonClient importing `worlds` back at
# that point is a circular import that breaks loading the whole apworld.
logger = logging.getLogger("Client")


def instance_id_for(slot_name: str | None) -> str:
    """Derives a filesystem-safe per-instance folder name from the connecting
    slot name, so each simultaneously-running client/PCSX2 pair gets its own
    ini/port/memcard instead of colliding on a shared one. Falls back to a fixed
    name if no slot name is known yet (e.g. launched before entering one)."""
    if not slot_name:
        return "default"
    return _UNSAFE_PATH_CHARS.sub("_", slot_name).strip(" .") or "default"


def _pid_is_our_pcsx2(pid_file: Path, pcsx2_exe_name: str) -> int | None:
    """The recorded pid, if it's still a live process running the configured
    PCSX2 executable - None if dead, unreadable, or reused by something else."""
    import psutil

    try:
        pid = int(pid_file.read_text().strip())
    except (ValueError, OSError):
        return None
    if not psutil.pid_exists(pid):
        return None
    try:
        if psutil.Process(pid).name().lower() != pcsx2_exe_name.lower():
            return None  # pid was reused by an unrelated process since we recorded it
    except psutil.Error:
        return None
    return pid


def _running_port_for(datapath: Path, config_path: Path, pcsx2_exe_name: str) -> int | None:
    """Returns the port our own previously-launched PCSX2 for this exact instance
    is listening on, if that specific process is still alive - or None if it's
    not running (or was never launched), meaning a fresh launch is needed.

    Process liveness via pid file rather than port probing on purpose: two
    instances can have the same port recorded in their stale inis (both
    defaulting to the same starting port when first configured), and a pure
    port-liveness check would wrongly conclude instance B is "already running"
    just because instance A's unrelated PCSX2 is listening on that port."""
    pid_file = datapath / _PID_FILENAME
    if not config_path.exists() or not pid_file.exists():
        return None
    if _pid_is_our_pcsx2(pid_file, pcsx2_exe_name) is None:
        return None
    return DynamicPineConfig.read_existing_port(config_path)


def prompt_for_iso(game_name: str, spec: DynamicPineGame) -> Path | None:
    """Asks the user to locate the game's ISO with a native file dialog and
    remembers the choice in host.yaml (via set_iso_path), so this only ever
    happens once per game. Returns None if they cancel or no dialog could be
    shown (e.g. headless)."""
    try:
        from Utils import open_filename
        chosen = open_filename(
            f"Locate ISO for {game_name} [{spec.game_id}]",
            (("PS2 images", (".iso", ".bin", ".chd", ".cso", ".gz")), ("All files", ("*",))),
        )
    except Exception as exc:
        logger.warning(f"[DynamicPine] Could not open a file dialog to locate the {game_name} ISO: {exc}")
        return None
    if not chosen:
        return None
    set_iso_path(spec, chosen)
    logger.info(f"[DynamicPine] Saved ISO for {game_name}: {chosen}")
    return Path(chosen)


def prompt_for_bios() -> Path | None:
    """Asks the user to locate their shared PCSX2 BIOS folder with a native
    folder dialog and remembers the choice in host.yaml (via set_bios_path), so
    this only ever needs doing once for every game/instance Dynamic Pine
    manages. Returns None if they cancel or no dialog could be shown (e.g.
    headless)."""
    try:
        from Utils import open_directory
        chosen = open_directory("Locate your PCSX2 BIOS folder")
    except Exception as exc:
        logger.warning(f"[DynamicPine] Could not open a folder dialog to locate the BIOS folder: {exc}")
        return None
    if not chosen:
        return None
    set_bios_path(chosen)
    logger.info(f"[DynamicPine] Saved BIOS folder: {chosen}")
    return Path(chosen)


def _reserved_ports(data_root: Path, pcsx2_exe_name: str) -> "set[int]":
    """Ports already promised to live Dynamic-Pine-launched PCSX2 instances,
    across every game under data_root (all games share one port space).

    This exists because a just-launched PCSX2 takes several seconds to actually
    bind its PINE port, so config-time is_pine_port_open probes can't see it
    yet - two launches in quick succession would both conclude the port is free
    and write the same PINESlot into their inis. pid files are written the
    moment a launch happens, so pid-liveness has no boot-time blind spot."""
    reserved: "set[int]" = set()
    if not data_root.is_dir():
        return reserved
    for game_dir in data_root.iterdir():
        if not game_dir.is_dir():
            continue
        for instance_dir in game_dir.iterdir():
            if not instance_dir.is_dir():
                continue
            if _pid_is_our_pcsx2(instance_dir / _PID_FILENAME, pcsx2_exe_name) is None:
                continue
            config_path = instance_dir / "PCSX2" / "inis" / "PCSX2.ini"
            if config_path.exists():
                reserved.add(DynamicPineConfig.read_existing_port(config_path))
    return reserved


@dataclasses.dataclass
class InstanceInfo:
    """One Dynamic-Pine-configured instance of a game, for the hub client's
    status display - whether or not its PCSX2 is currently running."""
    instance_id: str
    port: int
    running: bool
    pid: "int | None" = None


def list_instances(spec: DynamicPineGame) -> list[InstanceInfo]:
    """Every instance of this game that has ever been configured (has an ini
    under its data folder), whether or not its Dynamic-Pine-launched PCSX2
    process is still alive."""
    settings = dynamic_pine_settings()
    game_dir = Path(settings.pcsx2_data_path.resolve()) / spec.game_id
    pcsx2_name = Path(settings.pcsx2_path.resolve()).name
    if not game_dir.is_dir():
        return []

    instances: list[InstanceInfo] = []
    for instance_dir in sorted(game_dir.iterdir()):
        if not instance_dir.is_dir():
            continue
        config_path = instance_dir / "PCSX2" / "inis" / "PCSX2.ini"
        if not config_path.exists():
            continue
        pid = _pid_is_our_pcsx2(instance_dir / _PID_FILENAME, pcsx2_name)
        instances.append(InstanceInfo(instance_dir.name,
                                      DynamicPineConfig.read_existing_port(config_path),
                                      running=pid is not None, pid=pid))
    return instances


def list_running_instances(spec: DynamicPineGame) -> list[InstanceInfo]:
    """The subset of list_instances() whose PCSX2 process is still alive."""
    return [inst for inst in list_instances(spec) if inst.running]


def _rmtree_onerror(func, path, exc_info):
    """shutil.rmtree error hook: some files PCSX2 itself writes (e.g. under
    inis/debuggerlayouts) end up read-only, which blocks deletion on Windows
    with a plain PermissionError - clear the read-only attribute and retry
    the failed operation once before giving up."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_instance(spec: DynamicPineGame, instance_id: str) -> bool:
    """Deletes one instance's whole datapath (ini, memcard, pid file, save
    states - everything under it), freeing its port/instance_id for reuse.
    Refuses (raising InstanceAlreadyRunningError) if that instance's PCSX2 is
    currently running - stop it first. Returns False if there was nothing to
    remove."""
    settings = dynamic_pine_settings()
    data_root = Path(settings.pcsx2_data_path.resolve())
    pcsx2_name = Path(settings.pcsx2_path.resolve()).name
    datapath, _ = DynamicPineConfig.paths_for(data_root, spec.game_id, instance_id)
    if not datapath.exists():
        return False
    if _pid_is_our_pcsx2(datapath / _PID_FILENAME, pcsx2_name) is not None:
        raise InstanceAlreadyRunningError(
            f"Instance '{instance_id}' is still running - stop its PCSX2 before removing it."
        )
    shutil.rmtree(datapath, onerror=_rmtree_onerror)
    return True


def clear_unused_instances(spec: DynamicPineGame) -> list[str]:
    """Removes every configured instance of this game that isn't currently
    running, so leftover per-slot PCSX2 data (old test/one-off slot names,
    stale ports) doesn't accumulate forever. Running instances are left alone.
    An instance that fails to fully delete (e.g. a file still locked by
    another process) is logged and skipped rather than aborting the rest.
    Returns the instance_ids that were removed."""
    removed: list[str] = []
    for inst in list_instances(spec):
        if inst.running:
            continue
        try:
            if remove_instance(spec, inst.instance_id):
                removed.append(inst.instance_id)
        except OSError as exc:
            logger.warning(f"[DynamicPine] Could not remove instance '{inst.instance_id}': {exc}")
    return removed


def ensure_instance_config(world_or_game: "type[World] | str | DynamicPineGame",
                           slot_name: str | None = None) -> "DynamicPineConfig | None":
    """Builds (or reuses) this instance's PINE-enabled PCSX2 config - without
    launching PCSX2 itself - and records its port via mark_pine_port. Lets a
    client started through "Launch Client" alone (without also pressing
    "Launch PCSX2") still pick up its instance's ini/port/memcard immediately,
    the same way it would if launch_pcsx2 had already run for it.

    Does nothing (and returns None) if pcsx2_data_path isn't configured in
    host.yaml - that's the one setting this needs that launch_pcsx2 itself
    would otherwise be the first to check."""
    game_name, spec = resolve_game(world_or_game)
    settings = dynamic_pine_settings()

    try:
        data_root = Path(settings.pcsx2_data_path.resolve())
    except Exception:
        logger.warning(
            "[DynamicPine] pcsx2_data_path is not configured under dynamic_pine_options "
            "in host.yaml - the instance's PCSX2 config was not prepared."
        )
        return None
    bios_path = Path(settings.bios_path.resolve()) if settings.bios_path else None
    try:
        pcsx2_exe = Path(settings.pcsx2_path.resolve())
    except Exception:
        pcsx2_exe = None

    instance_id = instance_id_for(slot_name)
    reserved = _reserved_ports(data_root, pcsx2_exe.name) if pcsx2_exe is not None else None
    pine_config = DynamicPineConfig.for_dynamic_pine_game(
        data_root, spec.game_id, instance_id=instance_id, memcard_name=spec.memcard_name,
        bios_path=str(bios_path) if bios_path else None, ini_overrides=spec.ini_overrides,
        reserved_ports=reserved,
    )
    mark_pine_port(pine_config.port)
    logger.info(f"[DynamicPine] Prepared PCSX2 instance '{instance_id}' for {game_name} "
                f"(PINE port {pine_config.port}).")
    return pine_config


def launch_pcsx2(world_or_game: "type[World] | str | DynamicPineGame",
                 slot_name: str | None = None) -> int | None:
    """If this game+slot instance's PCSX2 isn't already running with PINE
    enabled, builds its PINE-enabled portable config (achievements off, own
    memcard/port, shared BIOS, plus the game's ini_overrides) and launches PCSX2
    with the ISO from dynamic_pine_options.game_files. Does nothing (and logs
    why) if the required host.yaml paths aren't configured.

    This is the one call a supported game's client needs to make. Returns the
    port PCSX2 will actually be listening on - which the caller must point its
    Pine connection at, since the config builder may have picked a port other
    than the one last used for this instance if that one was taken - or None if
    no launch was attempted and the caller should keep its current port.

    Instances are identified by slot_name (falling back to a fixed "default" if
    none is known yet), so multiple slots/players/games can each run their own
    PCSX2 at once without sharing a datapath, ini, memcard, or port.

    Raises InstanceAlreadyRunningError if this exact game+slot instance already
    has a live Dynamic-Pine-launched PCSX2 - callers that want to reconnect to
    it instead should look it up via list_instances()/get_pine_port() rather
    than calling launch_pcsx2 again.

    Does nothing at all - not even resolving/logging the game - unless this
    process was launched through the Dynamic Pine hub (see api.launched_via_hub):
    a game client started any other way (double-clicked from the AP Launcher,
    run directly from a shell, etc.) must fall back to its own pre-Dynamic-Pine
    behavior instead of silently taking over PCSX2 management."""
    if not launched_via_hub():
        logger.info(
            "[DynamicPine] Not launched through the Dynamic Pine hub client - "
            "skipping automatic PCSX2 management for this session."
        )
        return None

    game_name, spec = resolve_game(world_or_game)
    settings = dynamic_pine_settings()

    pcsx2_exe = Path(settings.pcsx2_path.resolve())
    data_root = Path(settings.pcsx2_data_path.resolve())
    bios_path = Path(settings.bios_path.resolve()) if settings.bios_path else None
    iso_file = get_iso_path(spec)

    if not pcsx2_exe.exists():
        logger.warning(
            "[DynamicPine] pcsx2_path is not configured (or not found) under "
            "dynamic_pine_options in host.yaml - start PCSX2 manually instead."
        )
        return None
    if iso_file is None or not iso_file.exists():
        # Game file not detected - prompt the user to find it once, then it's
        # remembered in host.yaml for every future launch.
        iso_file = prompt_for_iso(game_name, spec)
        if iso_file is None or not iso_file.exists():
            logger.warning(
                f"[DynamicPine] No ISO configured for {game_name} - add '{spec.game_id}: <path to ISO>' "
                "under game_files in dynamic_pine_options in host.yaml, or start PCSX2 manually."
            )
            return None

    instance_id = instance_id_for(slot_name)
    datapath, config_path = DynamicPineConfig.paths_for(data_root, spec.game_id, instance_id)

    running_port = _running_port_for(datapath, config_path, pcsx2_exe.name)
    if running_port is not None:
        raise InstanceAlreadyRunningError(
            f"PCSX2 instance '{instance_id}' for {game_name} is already running "
            f"(PINE port {running_port})."
        )

    try:
        pine_config = DynamicPineConfig.for_dynamic_pine_game(
            data_root, spec.game_id, instance_id=instance_id, memcard_name=spec.memcard_name,
            bios_path=str(bios_path) if bios_path else None, ini_overrides=spec.ini_overrides,
            reserved_ports=_reserved_ports(data_root, pcsx2_exe.name),
        )
        proc = subprocess.Popen(
            [str(pcsx2_exe), str(iso_file), "-batch", "-datapath", str(pine_config.datapath)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        (pine_config.datapath / _PID_FILENAME).write_text(str(proc.pid))
        logger.info(f"[DynamicPine] Launched PCSX2 instance '{instance_id}' for {game_name} "
                    f"(PINE port {pine_config.port}).")
        mark_pine_port(pine_config.port)
        return pine_config.port
    except OSError as exc:
        logger.warning(f"[DynamicPine] Failed to launch PCSX2: {exc}")
        return None

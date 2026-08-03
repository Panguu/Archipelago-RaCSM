"""Dynamic Pine's PCSX2 ini builder.

pypine (pinned at its "pine config builder" commit) provides the PINE protocol
and the base PineConfig, which handles enabling PINE on a port and pointing
Slot1 at a memcard. Everything multi-instance lives here on top of that:
per-instance portable datapaths grouped by game serial then slot name, port
reuse/probing so instances never collide, a shared BIOS folder so PCSX2's
first-run setup happens once, RetroAchievements disabled, and per-game
ini_overrides from the game's DynamicPineGame declaration.

The port/datapath logic is ported from rac_size_matters' extended pypine
working tree (its uncommitted additions to the same base commit)."""
from __future__ import annotations

import errno
import os
import platform
import socket
from configparser import ConfigParser
from pathlib import Path

# Import from the inner package: the submodule's top-level __init__ at this pin
# lists PineConfig in __all__ but doesn't actually import it.
from .pypine.pypine.config import DEFAULT_PINE_PORT, PineConfig

# Applied to every instance ini Dynamic Pine builds, after PineConfig's own
# PINE/memcard handling and before per-game ini_overrides. Consumers that need
# more than this add ini_overrides to their DynamicPineGame declaration instead
# of editing here.
BASE_INI_SETTINGS: dict[str, dict[str, str]] = {
    # RetroAchievements' hardcore mode blocks the savestates/cheats randomizer
    # play relies on, and randomized memory can trip its detection - always
    # fully off in Dynamic Pine instances.
    "Achievements": {
        "Enabled": "false",
        "ChallengeMode": "false",
    },
    # A brand new instance_id means a brand new, blank datapath, and both of
    # these matter only on that very first launch of it - confirmed against a
    # real PCSX2 by rac_size_matters/test/pcsx2_tests/harness.py:
    #  - SetupWizardIncomplete: without this, PCSX2 shows its interactive
    #    first-run setup wizard (EULA/welcome/GPU selection) and blocks
    #    forever waiting for someone to click through it - -batch/-datapath
    #    don't skip it on their own.
    #  - SettingsVersion: a hand-built ini has no opinion on this, so a fresh
    #    file leaves it unset/0. PCSX2 checks it and pops a blocking
    #    "Settings failed to load, or are the incorrect version - reset to
    #    defaults?" Yes/No confirmation dialog for ANY value it doesn't
    #    recognize as current. 1 is what PCSX2 itself writes once you click
    #    through that dialog by hand.
    # PCSX2 overwrites both to their "already seen it" values on its own after
    # the first launch, so re-applying them here every rebuild is harmless -
    # it just means an instance's very first launch never blocks on either
    # dialog waiting for someone to click through it by hand.
    "UI": {
        "SetupWizardIncomplete": "false",
        "SettingsVersion": "1",
    },
}


def _pine_socket_path(port: int) -> str:
    base_dir = os.environ.get("XDG_RUNTIME_DIR") or os.environ.get("TMPDIR") or "/tmp"
    name = "pcsx2.sock" if port == DEFAULT_PINE_PORT else f"pcsx2.sock.{port}"
    return os.path.join(base_dir, name)


def is_pine_port_open(port: int) -> bool:
    """True if a PINE server (a running PCSX2 instance) is already listening on
    this port. On Windows this is a TCP bind probe; on Linux/macOS it checks (and
    connects to) the platform's PINE unix socket file, cleaning up stale sockets
    left behind by a PCSX2 process that didn't shut down cleanly."""
    if platform.system() == "Windows":
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return False
            except OSError:
                return True

    sock_path = _pine_socket_path(port)
    if not os.path.exists(sock_path):
        return False

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.connect(sock_path)
            return True
    except OSError as e:
        if e.errno in (errno.ECONNREFUSED, errno.ENOENT):
            try:
                os.remove(sock_path)
            except OSError:
                pass
        return False


def find_free_port(start: int = 28021, end: int = 28031, exclude: "set[int] | None" = None) -> int:
    """Finds a PINE port with no emulator currently listening on it and not in
    exclude (ports promised to still-booting instances that aren't listening
    yet - see launcher._reserved_ports), falling back to DEFAULT_PINE_PORT if
    the whole range is somehow occupied."""
    exclude = exclude or set()
    for port in range(start, end + 1):
        if port in exclude:
            continue
        if not is_pine_port_open(port):
            return port
    return DEFAULT_PINE_PORT


class DynamicPineConfig(PineConfig):
    """PineConfig plus everything Dynamic Pine layers on: per-instance portable
    datapath, shared BIOS folder, base settings (achievements off), and a game's
    ini_overrides - all re-applied on every (re)build of the instance's
    PCSX2.ini, so user edits to managed keys self-correct on the next launch."""

    def __init__(self, config_path: Path, port: int = DEFAULT_PINE_PORT, memcard_name: str = "memcard.ps2",
                 bios_path: str | None = None, datapath: Path | None = None,
                 ini_overrides: dict[str, dict[str, str]] | None = None):
        super().__init__(config_path, port=port, memcard_name=memcard_name)
        # PCSX2 reads its settings from "<datapath>/inis/PCSX2.ini" - datapath
        # itself is what gets passed to -datapath, which is config_path's
        # grandparent in the paths_for() layout. Defaults to the immediate
        # parent for standalone/manual use outside that layout.
        self.datapath = datapath if datapath is not None else config_path.parent
        self.bios_path = bios_path
        self.ini_overrides: dict[str, dict[str, str]] = ini_overrides or {}

    @staticmethod
    def read_existing_port(config_path: Path) -> int:
        existing = ConfigParser(delimiters=('='))
        existing.optionxform = str
        existing.read(config_path)
        try:
            return int(existing.get('EmuCore', 'PINESlot', fallback=DEFAULT_PINE_PORT))
        except ValueError:
            return DEFAULT_PINE_PORT

    @staticmethod
    def paths_for(data_root: Path, game_id: str, instance_id: str = "default") -> tuple[Path, Path]:
        """Returns (datapath, config_file_path) for one instance of a game,
        without touching the filesystem - shared by for_dynamic_pine_game() and
        by callers (e.g. the launcher) that need to inspect an instance's
        config/pid files before deciding whether to build/launch anything.

        -datapath overrides where PCSX2 treats its "Documents" root as being,
        but PCSX2 still nests its own "PCSX2/" app folder underneath that (same
        as its normal non-portable "Documents/PCSX2/inis/PCSX2.ini" layout) -
        confirmed by inspecting real PCSX2 output folders, which populated
        "<datapath>/PCSX2/inis/PCSX2.ini" every time and left a flat
        "<datapath>/inis/PCSX2.ini" untouched. Without that extra "PCSX2"
        segment here, we'd be writing PINE settings into a file PCSX2 never
        reads."""
        instance_dir = data_root / game_id / instance_id
        return instance_dir, instance_dir / "PCSX2" / "inis" / "PCSX2.ini"

    @classmethod
    def for_dynamic_pine_game(cls, data_root: Path, game_id: str, instance_id: str = "default",
                              memcard_name: str = "memcard.ps2", bios_path: str | None = None,
                              ini_overrides: dict[str, dict[str, str]] | None = None,
                              reserved_ports: "set[int] | None" = None,
                              ) -> "DynamicPineConfig":
        """Builds (or reuses) a PINE-enabled PCSX2.ini for one instance of a game,
        in a subfolder of data_root named after the game's serial (e.g. SCUS-97615)
        and then the instance_id (e.g. a slot/player name), so running several
        instances - of the same game or different ones - never share a portable
        PCSX2 data directory, ini, memcard, or PINE port with each other.

        Reuses the port from an existing config for this instance if present and
        not currently in use by another emulator instance; otherwise picks a fresh
        free port so this instance never collides with one already running (e.g.
        started manually, or by a different client/instance).

        reserved_ports covers the blind spot of the listening probe: ports in
        inis of other live launched instances whose PCSX2 is still booting and
        hasn't bound its PINE port yet. Without it, two launches in quick
        succession both see the port "free" and end up sharing it."""
        datapath, config_path = cls.paths_for(data_root, game_id, instance_id)
        port = cls.read_existing_port(config_path) if config_path.exists() else DEFAULT_PINE_PORT

        reserved = reserved_ports or set()
        if port in reserved or is_pine_port_open(port):
            port = find_free_port(exclude=reserved)

        instance = cls(config_path, port=port, memcard_name=memcard_name, bios_path=bios_path,
                       datapath=datapath, ini_overrides=ini_overrides)
        instance.setup_config()
        return instance

    def _verify_config(self):
        super()._verify_config()
        # Each instance gets its own blank datapath, which would otherwise trigger
        # PCSX2's first-run BIOS setup wizard every time a new instance is created.
        # Pointing every instance at one shared BIOS folder avoids that repeat setup.
        if self.bios_path:
            self._normalize_keys('Folders', {'bios': 'Bios'})
            self.config['Folders'] = {
                **self.config['Folders'],
                'Bios': self.bios_path,
            }
        for source in (BASE_INI_SETTINGS, self.ini_overrides):
            for section, values in source.items():
                if not self.config.has_section(section):
                    self.config.add_section(section)
                self.config[section] = {**self.config[section], **values}

import errno
import os
import platform
import socket
from configparser import ConfigParser
from pathlib import Path

from .pypine.pypine.config import DEFAULT_PINE_PORT, PineConfig
from .types import Overrides

BASE_INI_SETTINGS: Overrides = {
    "Achievements": {
        "Enabled": "false",
        "ChallengeMode": "false",
    },
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
        # Stale socket left by a PCSX2 that didn't shut down cleanly
        if e.errno in (errno.ECONNREFUSED, errno.ENOENT):
            try:
                os.remove(sock_path)
            except OSError:
                pass
        return False


def find_free_port(start: int = 28021, end: int = 28031, exclude: set[int] | None = None) -> int:
    exclude = exclude or set()
    for port in range(start, end + 1):
        if port in exclude:
            continue
        if not is_pine_port_open(port):
            return port
    return DEFAULT_PINE_PORT


class DynamicPineConfig(PineConfig):
    def __init__(self, config_path: Path, port: int = DEFAULT_PINE_PORT, memcard_name: str = "memcard.ps2",
                 bios_path: str | None = None, datapath: Path | None = None,
                 ini_overrides: Overrides | None = None):
        super().__init__(config_path, port=port, memcard_name=memcard_name)
        self.datapath = datapath if datapath is not None else config_path.parent
        self.bios_path = bios_path
        self.ini_overrides: Overrides = ini_overrides or {}

    @staticmethod
    def read_existing_port(config_path: Path) -> int:
        existing = ConfigParser(delimiters=("="))
        existing.optionxform = str
        existing.read(config_path)
        try:
            return int(existing.get("EmuCore", "PINESlot", fallback=DEFAULT_PINE_PORT))
        except ValueError:
            return DEFAULT_PINE_PORT

    @staticmethod
    def paths_for(data_root: Path, game_id: str, instance_id: str = "default") -> tuple[Path, Path]:
        # PCSX2 nests its own "PCSX2/" folder under -datapath, so the ini lives there
        instance_dir = data_root / game_id / instance_id
        return instance_dir, instance_dir / "PCSX2" / "inis" / "PCSX2.ini"

    @classmethod
    def for_dynamic_pine_game(cls, data_root: Path, game_id: str, instance_id: str = "default",
                              memcard_name: str = "memcard.ps2", bios_path: str | None = None,
                              ini_overrides: Overrides | None = None,
                              reserved_ports: set[int] | None = None,
                              ) -> "DynamicPineConfig":
        datapath, config_path = cls.paths_for(data_root, game_id, instance_id)
        port = cls.read_existing_port(config_path) if config_path.exists() else DEFAULT_PINE_PORT

        # reserved_ports covers instances still booting that haven't bound their port yet
        reserved = reserved_ports or set()
        if port in reserved or is_pine_port_open(port):
            port = find_free_port(exclude=reserved)

        instance = cls(config_path, port=port, memcard_name=memcard_name, bios_path=bios_path,
                       datapath=datapath, ini_overrides=ini_overrides)
        instance.setup_config()
        return instance

    def _verify_config(self):
        super()._verify_config()
        if self.bios_path:
            self._normalize_keys("Folders", {"bios": "Bios"})
            self.config["Folders"] = {
                **self.config["Folders"],
                "Bios": self.bios_path,
            }
        for source in (BASE_INI_SETTINGS, self.ini_overrides):
            for section, values in source.items():
                if not self.config.has_section(section):
                    self.config.add_section(section)
                self.config[section] = {**self.config[section], **values}

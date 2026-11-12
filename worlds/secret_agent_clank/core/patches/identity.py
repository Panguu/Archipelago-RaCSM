"""PCSX2 reports the boot ELF's CRC (an XOR of its 32-bit words), not a checksum
of the ISO, so loaded code is checked as well to catch stale savestates.
"""
from dataclasses import dataclass
import hashlib
import struct


GAME_ID = "SCUS-97623"
STAMP_MAGIC = b"SACAPISO"


class WrongPatchedGame(RuntimeError):
    pass


def executable_crc(data: bytes) -> str:
    value = 0
    for (word,) in struct.iter_unpack("<I", data[:len(data) // 4 * 4]):
        value ^= word
    return f"{value:08x}"


def stamp_executable(data: bytes, *, build_id: str, abi: int) -> bytes:
    """Append the build ID after the ELF data, where the game never loads it."""
    if len(data) < 52 or data[:7] != b"\x7fELF\x01\x01\x01":
        raise ValueError("Expected ELF32 executable")
    if type(abi) is not int or not 0 < abi <= 65535 or not build_id:
        raise ValueError("Invalid SAC build identity")
    if STAMP_MAGIC in data[-64:]:
        raise ValueError("Executable already has an SAC build stamp")
    stamp = STAMP_MAGIC + struct.pack("<II", 1, abi) + hashlib.sha256(build_id.encode("utf-8")).digest()
    result = data + bytes((-len(data)) % 4) + stamp
    # Make sure the patched ELF can't have the same CRC as the clean one.
    if executable_crc(result) == executable_crc(data):
        result += struct.pack("<I", 1)
    return result


def read_pcsx2_crc(pine) -> str:
    """Ask PCSX2 for the boot ELF's CRC over the existing PINE connection."""
    response = pine._send_request(struct.pack("<IB", 5, 0x0D))
    if (len(response) != 18 or struct.unpack_from("<I", response)[0] != len(response)
            or response[4] != 0 or struct.unpack_from("<I", response, 5)[0] != 9
            or response[-1] != 0):
        raise WrongPatchedGame("PCSX2 returned an invalid game CRC")
    try:
        crc = response[9:-1].decode("ascii").lower()
    except UnicodeDecodeError as exc:
        raise WrongPatchedGame("PCSX2 returned an invalid game CRC") from exc
    if any(c not in "0123456789abcdef" for c in crc):
        raise WrongPatchedGame("PCSX2 returned an invalid game CRC")
    return crc


@dataclass(frozen=True)
class CodeProbe:
    address: int
    expected: bytes

    def __post_init__(self):
        if (type(self.address) is not int or not self.expected or len(self.expected) > 4096
                or not 0x100000 <= self.address <= 0x2000000 - len(self.expected)):
            raise ValueError("Invalid resident code probe")


@dataclass(frozen=True)
class PatchedGameGuard:
    build_id: str
    elf_crc: str
    resident_probes: tuple[CodeProbe, ...]

    def __post_init__(self):
        if (not self.build_id or len(self.elf_crc) != 8
                or any(c not in "0123456789abcdef" for c in self.elf_crc)
                or not self.resident_probes):
            raise ValueError("Incomplete patched-game identity")

    def verify(self, pine) -> None:
        """Check PCSX2 is running this patched build. Run before any write, and
        again after a reset or savestate load."""
        if pine.get_game_id() != GAME_ID:
            raise WrongPatchedGame("PCSX2 is not running Secret Agent Clank (USA)")
        if read_pcsx2_crc(pine) != self.elf_crc:
            raise WrongPatchedGame(f"Load the Archipelago ISO for build {self.build_id}; disc identity differs")
        for probe in self.resident_probes:
            if pine.read_bytes(probe.address, len(probe.expected)) != probe.expected:
                raise WrongPatchedGame("Loaded code differs from the patched ISO; cold boot the patched game")
        if pine.get_game_id() != GAME_ID or read_pcsx2_crc(pine) != self.elf_crc:
            raise WrongPatchedGame("PCSX2 changed games during patched-ISO validation")

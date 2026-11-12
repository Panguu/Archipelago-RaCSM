"""Free space added to the end of a level module for new code and data."""
import struct

from .asm import Patch
from .snr2 import InvalidModule, SNR2Module


def reserve_arena(data: bytes, size: int = 65536) -> tuple[bytes, int]:
    SNR2Module(data)
    if type(size) is not int or size <= 0 or size % 16 or size > 1024 * 1024:
        raise InvalidModule("Invalid module arena size")
    start = (len(data) + 15) & ~15
    result = bytearray(data)
    result.extend(bytes(start + size - len(result)))
    struct.pack_into("<I", result, 44, len(result))
    return bytes(result), start


class ModuleArena:
    def __init__(self, base: int, loaded: bytes, start: int):
        if start % 16 or start < 128 or start >= len(loaded) or any(loaded[start:]):
            raise InvalidModule("Expected an empty module arena")
        self.base, self.loaded, self.start = base, loaded, start
        self.cursor = start
        self.patches: list[Patch] = []

    def allocate(self, data: bytes, *, alignment: int = 16) -> int:
        if alignment not in (4, 8, 16, 32, 64) or not data:
            raise InvalidModule("Invalid arena allocation")
        offset = (self.cursor + alignment - 1) & -alignment
        payload = bytes(data) + bytes((-len(data)) % 4)
        end = offset + len(payload)
        if end > len(self.loaded):
            raise InvalidModule("Native module arena exhausted")
        self.patches.append(Patch(self.base + offset, self.loaded[offset:end], payload))
        self.cursor = end
        return self.base + offset

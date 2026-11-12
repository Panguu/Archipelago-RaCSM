import struct
from dataclasses import dataclass

from ..batch_io import read_blocks

MARKER = b"SAC_LOC_HOOK_V1\0"


def words(data):
    return list(struct.unpack("<" + "I" * (len(data) // 4), data))


def packed(values):
    return struct.pack("<" + "I" * len(values), *values)


def jump(address, link=False):
    if address % 4:
        raise ValueError("MIPS jump target must be word aligned")
    return (0x0C000000 if link else 0x08000000) | (address >> 2)


def branch(source, target):
    return 0x10000000 | (((target - source - 4) // 4) & 0xFFFF)


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


@dataclass(frozen=True)
class Patch:
    address: int
    original: bytes
    replacement: bytes


def capture(pine, edits):
    originals = read_blocks(pine, [(address, len(replacement)) for address, replacement in edits])
    return [Patch(address, original, replacement) for (address, replacement), original in zip(edits, originals)]

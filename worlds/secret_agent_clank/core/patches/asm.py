"""Shared low-level MIPS/patch-plan primitives -- word packing, jump/branch encoding, and the Patch record every patches/*.py plan builder produces."""
import struct
from dataclasses import dataclass

if not __debug__:
    raise RuntimeError("Native hook validation must not run with Python assertions disabled")

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


@dataclass(frozen=True)
class Patch:
    address: int
    original: bytes
    replacement: bytes

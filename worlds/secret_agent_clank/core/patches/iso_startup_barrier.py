"""The resident loader waits while the level's relocation status is -1. The ISO
sends that check through a routine in free executable space instead:

- not armed (at boot, or with no client): the original status check;
- armed: keep waiting until the client writes -1 to REQUEST.

Arming is a lease the loader counts down on each check and the client renews
every poll, so a crashed client only holds a load until the lease runs out.
"""
import struct

from . import mips as m
from .asm import jump, packed
from .loader_state import LoaderStateReader, StartupBarrierLost

REQUEST = 0x206324
SITE_RETURN = LoaderStateReader.SIGNATURE_START + 8  # the original "li a0, -1; beq v0, a0, wait"
ROUTINE_SIZE = 15 * 4  # 14 instructions, then the lease word
LEASE = 600  # loader checks, about once a frame: roughly 10 seconds


def _hi_lo(address: int) -> tuple[int, int]:
    """lui/lw halves; lw sign-extends its offset, so carry into the upper half."""
    return (address + 0x8000) >> 16, address & 0xFFFF


def site_code(routine: int) -> bytes:
    """The loader site: jump to the routine instead of calling the status getter."""
    return packed([jump(routine), m.NOP, *LoaderStateReader.SIGNATURE[2:]])


def routine_code(routine: int) -> bytes:
    arm_hi, arm_lo = _hi_lo(routine + ROUTINE_SIZE - 4)
    status_hi, status_lo = _hi_lo(LoaderStateReader.STATUS)
    request_hi, request_lo = _hi_lo(REQUEST)
    # a0 is free: the original code sets it to -1 straight after the site.
    return packed([
        m.lui(m.V1, arm_hi),
        m.lw(m.A0, arm_lo, m.V1),      # checks left on the lease
        m.beq(m.A0, m.ZERO, 9),        # not armed, or the lease ran out: go to the original check
        m.lui(m.V0, status_hi),        # (delay slot)
        m.addiu(m.A0, m.A0, -1),
        m.sw(m.A0, arm_lo, m.V1),      # use up one check
        m.lui(m.V0, request_hi),
        m.lw(m.V0, request_lo, m.V0),
        m.addiu(m.V0, m.V0, 1),        # 0 once the client has released (REQUEST == -1)
        m.sltu(m.V0, m.ZERO, m.V0),    # 1 while still held
        jump(SITE_RETURN),
        m.sub_(m.V0, m.ZERO, m.V0),    # -1 while held, so the original check keeps waiting
        jump(SITE_RETURN),             # not armed: carry on with the original check...
        m.lw(m.V0, status_lo, m.V0),   # ...on v0 = relocation status, as the getter returns
        0,                             # lease word: 0 at boot, renewed by the client
    ])


class ISOStartupBarrier(LoaderStateReader):
    REQUEST = REQUEST

    def __init__(self, pine, routine: int):
        super().__init__(pine)
        self.routine = routine
        self.arm_address = routine + ROUTINE_SIZE - 4
        self.code = site_code(routine)
        self.routine_code = routine_code(routine)[:-4]  # without the lease word, which changes

    def validate(self, *, patched=False):
        if self.pine.get_game_id() != "SCUS-97623":
            raise StartupBarrierLost("Game changed; permanent loader unavailable")
        if (self.pine.read_bytes(self.SIGNATURE_START, len(self.code)) != self.code
                or self.pine.read_bytes(self.routine, len(self.routine_code)) != self.routine_code):
            raise StartupBarrierLost("Permanent loader code differs; reset or incompatible savestate")

    def attach(self):
        """Called every poll, which also re-arms after a game reset."""
        self.validate()
        self.pine.write_int32(self.arm_address, LEASE)
        if not self.attached:
            self.attached = True
            self._held_candidate = None

    def held_module(self, *, settled=False):
        """The loading level, only while it's waiting on REQUEST."""
        target = super().held_module(settled=settled)
        if target is not None and self.pine.read_int32(self.REQUEST) != target:
            self._held_candidate = None
            return None
        return target

    def release(self):
        if not self.attached:
            return
        if self.held_module() is None:
            raise StartupBarrierLost("Cannot release a loader without a stable relocated module")
        self.pine.write_int32(self.REQUEST, 0xFFFFFFFF)
        self._held_candidate = None

    def detach(self, *, disarm=True):
        """Pass disarm=False when memory failed verification, so nothing is written."""
        was_attached, self.attached = self.attached, False
        self._held_candidate = None
        if disarm and was_attached:
            self.pine.write_int32(self.arm_address, 0)


def find_routine_space(data: bytes) -> int:
    """Address of linker padding in a loaded, executable part of the ELF for the routine.

    Uses the gaps between allocated sections: bytes the game loads but that no
    section, and so no code or data, occupies. They must be zero in the file.
    """
    shoff = struct.unpack_from("<I", data, 32)[0]
    shentsize, shnum = struct.unpack_from("<HH", data, 46)
    if not shoff or shentsize != 40 or not shnum or shoff + shentsize * shnum > len(data):
        raise ValueError("Executable has no section headers to find free space with")
    sections = []
    for index in range(shnum):
        _, kind, flags, address, _, size, *_ = struct.unpack_from("<10I", data, shoff + index * 40)
        if flags & 2 and kind != 8 and size:  # SHF_ALLOC, not SHT_NOBITS
            sections.append((address, address + size))
    sections.sort()

    phoff = struct.unpack_from("<I", data, 28)[0]
    phentsize, phnum = struct.unpack_from("<HH", data, 42)
    for index in range(phnum):
        kind, offset, start, _, filesz, _, flags, _ = struct.unpack_from("<8I", data, phoff + index * phentsize)
        if kind != 1 or not flags & 1:  # executable PT_LOAD segments only
            continue
        end = start + filesz
        inside = [(max(a, start), min(b, end)) for a, b in sections if a < end and b > start]
        # A gap runs from the end of one section to the next section (or the segment end).
        for (_, gap_start), next_start in zip(inside, [a for a, _ in inside[1:]] + [end]):
            gap_start = (gap_start + 7) & ~7
            if next_start - gap_start >= ROUTINE_SIZE:
                file_start = offset + gap_start - start
                if not any(data[file_start:file_start + ROUTINE_SIZE]):
                    return gap_start
    raise ValueError("No free space in the executable for the loader routine")


def patch_resident_loader(data: bytes) -> tuple[bytes, int]:
    """Install the barrier. Returns the patched executable and the routine's address."""
    if len(data) < 52 or data[:7] != b"\x7fELF\x01\x01\x01":
        raise ValueError("Expected ELF32 little-endian executable")
    phoff = struct.unpack_from("<I", data, 28)[0]
    size, count = struct.unpack_from("<HH", data, 42)
    if size != 32 or not count or phoff + size * count > len(data):
        raise ValueError("Invalid ELF program headers")
    segments = []
    for index in range(count):
        kind, offset, virtual, _, filesz, memsz, flags, _ = struct.unpack_from("<8I", data, phoff + size * index)
        if kind != 1:
            continue
        if filesz > memsz or offset + filesz > len(data):
            raise ValueError("Invalid ELF load segment")
        segments.append((offset, virtual, filesz, flags))

    def file_offset(address: int, length: int) -> int:
        matches = [offset + address - virtual for offset, virtual, filesz, flags in segments
                   if virtual <= address and address + length <= virtual + filesz and flags & 1]
        if len(matches) != 1:
            raise ValueError(f"{address:#x} must map to exactly one executable ELF segment")
        return matches[0]

    site = file_offset(LoaderStateReader.SIGNATURE_START, 44)
    original = struct.pack("<11I", *LoaderStateReader.SIGNATURE)
    if data[site:site + len(original)] != original:
        raise ValueError("Resident loader signature differs from clean SCUS-97623")
    routine = find_routine_space(data)
    result = bytearray(data)
    result[site:site + len(original)] = site_code(routine)
    start = file_offset(routine, ROUTINE_SIZE)
    result[start:start + ROUTINE_SIZE] = routine_code(routine)
    return bytes(result), routine

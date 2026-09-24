"""Reversible execution-counter hook for validating a PSP frame profile.

This diagnostic hook changes no gameplay state. It preserves temporary
registers, increments an owned counter, and replays the captured prologue.
"""
import struct

from .code import CodePlan
from .plan import Patch


def jump(source, destination):
    if source % 4 or destination % 4 or (source + 4) >> 28 != destination >> 28:
        raise ValueError("MIPS jump requires aligned addresses in the same segment")
    return 0x08000000 | ((destination >> 2) & 0x03ffffff)


def counter_payload(address, counter, entry, original):
    # Only replay the verified pair: addiu sp,sp,-N followed by lui a0,imm.
    # Branches and PC-relative instructions require relocation, not copying.
    if len(original) != 8:
        raise ValueError("Expected two captured prologue instructions")
    first, second = struct.unpack("<II", original)
    if first >> 16 != 0x27bd or not first & 0x8000 or second >> 16 != 0x3c04:
        raise ValueError("Unsupported frame prologue")
    if counter % 4:
        raise ValueError("Counter must be word aligned")
    high = ((counter + 0x8000) >> 16) & 0xffff
    low = counter & 0xffff
    words = [
        0x27bdfff0,  # addiu sp,sp,-16
        0xafa80000,  # sw t0,0(sp)
        0xafa90004,  # sw t1,4(sp)
        0x3c080000 | high,
        0x8d090000 | low,
        0x25290001,  # addiu t1,t1,1
        0xad090000 | low,
        0x8fa80000,
        0x8fa90004,
        0x27bd0010,
        first, second,
        jump(address + 48, entry + 8),
        0,
    ]
    return struct.pack("<14I", *words)


class CounterHook:
    def __init__(self, memory, storage, entry, original, *, planet_id):
        self.memory, self.storage = memory, storage
        self.entry, self.original, self.planet_id = entry, original, planet_id
        self.plan = None
        self.counter = None
        self.code = None

    def install(self):
        if self.plan is not None:
            raise RuntimeError("Counter hook already prepared")
        with self.memory.paused():
            self.memory.invalidate_code()
            if self.memory.read_bytes(self.entry, len(self.original)) != self.original:
                raise RuntimeError("Frame prologue does not match PSP profile")
            code = self.storage.reserve("frame-counter-code", 56)
            self.code = code
            self.counter = self.storage.reserve("frame-counter-data", 4)
            payload = counter_payload(code.address, self.counter.address, self.entry, self.original)
            self.storage.write(code.name, payload)
            replacement = struct.pack("<II", jump(self.entry, code.address), 0)
            self.plan = CodePlan(self.memory, [Patch(self.entry, self.original, replacement)],
                                 name="PSP frame counter", planet_id=self.planet_id)
            self.storage.retain(self)
            # Retain even on failed installation: rollback might itself fail.
            # restore() verifies original bytes before releasing that reference.
            self.plan.install()

    def restore(self):
        if self.plan is None:
            return
        with self.memory.paused():
            status = self.memory._control._request("cpu.status")
            if self.code.address <= status["pc"] < self.code.address + self.code.size:
                raise RuntimeError("CPU is executing the hook; reach the return boundary before restoring")
            self.memory.invalidate_code()
            self.plan.restore()
            self.plan.validate(False)
            self.storage.release(self)

    def count(self):
        if self.counter is None:
            raise RuntimeError("Counter hook has not been installed")
        self.storage.validate()
        return self.memory.read_int32(self.counter.address)

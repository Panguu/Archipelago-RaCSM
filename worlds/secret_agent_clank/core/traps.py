"""Timed native cheats, resolved from the current module rather than fixed RAM."""
import struct
import time

from ..constants.cheats import SACTraps, TRAP_DURATIONS
from .case_menu import ee_pointer

# Verified CHEAT_IsActive callers: clip matrix, GrantBolts, head scaling,
# and CHEAT_Update/CanSelectWeapon respectively.
TRAP_BITS = {
    SACTraps.BIG_HEADED: (1 << 1) | (1 << 2),
    SACTraps.MIRRORED_LEVELS: 1 << 3,
    SACTraps.BOLT_CONFUSION: 1 << 5,
    SACTraps.WEAPON_SWITCHING: 1 << 6,
}


def absolute(hi, low):
    low &= 0xFFFF
    return ((hi & 0xFFFF) << 16) + (low - 0x10000 if low & 0x8000 else low)


class Traps:
    def __init__(self, pine, clock=time.monotonic):
        self.pine = pine
        self.clock = clock
        self.durations = dict(TRAP_DURATIONS)
        self.remaining = {}
        self.original = 0
        self.managed = 0
        self.last_tick = None

    def address(self, symbols):
        function = symbols.get("CHEAT_IsActive__FUi")
        if function is None:
            return None
        w = struct.unpack("<8I", self.pine.read_bytes(function, 32))
        if (w[0] & 0xFFFF0000 != 0x3C020000 or w[1] != 0x24030001
                or w[2] & 0xFFFF0000 != 0x8C450000
                or w[3:] != (0x00831804, 0x8CA208E0, 0x00431024, 0x03E00008, 0x0002102B)):
            raise RuntimeError("Native cheat reader layout changed")
        root = self.pine.read_int32(absolute(w[0], w[2]))
        return root + 0x8E0 if ee_pointer(root, 0x8E4) else None

    def switching_timer(self, symbols):
        # Mirror the only nonempty activation callback used by these traps.
        function = symbols.get("CHEAT_Activate__FUi")
        if function is None:
            raise RuntimeError("Native cheat activation routine missing")
        w = struct.unpack("<7I", self.pine.read_bytes(function, 28))
        if (w[:3] != (0x27BDFFF0, 0x24030014, 0xFFB00000)
                or w[3] & 0xFFFF0000 != 0x3C020000 or w[4] != 0x0080802D
                or w[5] & 0xFFFF0000 != 0x24420000):
            raise RuntimeError("Native cheat activation layout changed")
        table = absolute(w[3], w[5])
        if not ee_pointer(table, 7 * 20):
            raise RuntimeError("Invalid native cheat table")
        callback = self.pine.read_int32(table + 6 * 20 + 16)
        if not ee_pointer(callback, 24):
            raise RuntimeError("Invalid weapon switching callback")
        w = struct.unpack("<6I", self.pine.read_bytes(callback, 24))
        if (w[0] != 0x10800003 or w[1] & 0xFFFF0000 != 0x3C030000
                or w[2] != 0x24020168 or w[3] & 0xFFFF0000 != 0xAC620000
                or w[4:] != (0x03E00008, 0)):
            raise RuntimeError("Weapon switching callback changed")
        return absolute(w[1], w[3])

    def activate(self, name, symbols):
        address = self.address(symbols)
        if address is None:
            return False
        bits = TRAP_BITS[name]
        timer = self.switching_timer(symbols) if name == SACTraps.WEAPON_SWITCHING else None
        current = self.pine.read_int32(address)
        new_bits = bits & ~self.managed
        original = (self.original & ~new_bits) | (current & new_bits)
        if timer is not None:
            self.pine.write_int32(timer, 360)
        self.pine.write_int32(address, current | bits)
        self.original = original
        self.managed |= bits
        self.remaining[name] = self.remaining.get(name, 0) + self.durations.get(name, 30)
        self.last_tick = self.clock()
        return True

    def restore(self, symbols):
        if not self.managed:
            return
        address = self.address(symbols)
        if address is None:
            return
        current = self.pine.read_int32(address)
        self.pine.write_int32(address, (current & ~self.managed) | self.original)
        self.remaining.clear()
        self.managed = self.original = 0
        self.last_tick = None

    def tick(self, symbols, playing):
        now = self.clock()
        elapsed = min(0.5, max(0, now - self.last_tick)) if self.last_tick is not None and playing else 0
        self.last_tick = now if playing else None
        if not self.managed or not playing:
            return
        address = self.address(symbols)
        if address is None:
            return
        remaining = {name: seconds - elapsed for name, seconds in self.remaining.items()}
        active = 0
        for name, seconds in remaining.items():
            if seconds > 0:
                active |= TRAP_BITS[name]
        expired = self.managed & ~active
        current = self.pine.read_int32(address)
        self.pine.write_int32(address, (current & ~expired) | (self.original & expired) | active)
        self.remaining = {name: seconds for name, seconds in remaining.items() if seconds > 0}
        self.managed = active
        self.original &= active

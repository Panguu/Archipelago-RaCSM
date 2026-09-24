"""Ratchet-only wrench input gates and progressive native mod entitlements."""
import struct

from ...constants.native_functions import NativeFunctions
from ..symbols import require
from .asm import Patch
from .patch import PatchSet

PROGRESSIVE_WRENCH = "Progressive Wrench"
WRENCH_MODS = ("wrenchpower_firebomb", "wrenchpower_triplewave",
              "wrenchpower_crystallix", "wrenchpower_wildburst")
RATCHET_MODULES = {3, 9, 14, 21, 25}


class WrenchProgression(PatchSet):
    def __init__(self, pine):
        super().__init__(pine)
        self.enabled = False
        self.count = 0
        self.module = None
        self.sites = []
        self.power_address = None

    def entitlements(self):
        return {name: self.count >= index + 2 for index, name in enumerate(WRENCH_MODS)} if self.enabled else {}

    def prepare(self, symbols, module):
        self.patches = []
        self.module, self.sites = module, []
        self.power_address = None
        if not self.enabled or module not in RATCHET_MODULES:
            return []
        # These masks consume only the wrench button. Gun, movement, jump,
        # and camera masks are untouched. Resolve each Ratchet-only export.
        specs = (
            (NativeFunctions.RATCHET_UPDATE_CONTROLS_NORMAL_ACTION_BUTTONS, 0x538, 0x27BDFFC0, 0x30A20020, 2),
            (NativeFunctions.RATCHET_UPDATE_CONTROLS_CROUCH_ACTION_BUTTONS, 0x228, 0x27BDFFE0, 0x30420020, 1),
            (NativeFunctions.RATCHET_CHECK_JUMP_ATTACK, 0x158, 0x27BDFFE0, 0x30420020, 1),
        )
        for name, size, prologue, mask, expected in specs:
            address = require(symbols, name)
            if self.pine.read_int32(address) != prologue:
                raise RuntimeError(f"Unrecognized Ratchet wrench gate: {name}")
            code = struct.unpack("<" + "I" * (size // 4), self.pine.read_bytes(address, size))
            sites = [(address + i * 4, word) for i, word in enumerate(code) if word == mask]
            if len(sites) != expected:
                raise RuntimeError(f"Ratchet wrench input layout changed: {name}")
            self.sites.extend(sites)
        self.power_address = require(symbols, "g_wrench_wrenchPower")
        self.patches = [Patch(a, struct.pack("<I", word), struct.pack("<I", word if self.count else word & 0xFFFF0000))
                for a, word in self.sites]
        return self.patches

    def sync(self):
        if not self.enabled or not self.sites:
            return
        if (self.pine.read_int32(0x206328) != self.module
                or self.pine.read_int32(0x206324) != 0xFFFFFFFF):
            return
        for address, original in self.sites:
            current = self.pine.read_int32(address)
            if current not in (original, original & 0xFFFF0000):
                raise RuntimeError("Wrench gate changed; refusing an unknown code write")
        # Previously selected vanilla mods must not bypass AP ownership.
        if self.power_address is not None:
            selected = self.pine.read_int32(self.power_address)
            if selected > max(0, self.count - 1):
                self.pine.write_int32(self.power_address, 0)
        # Each write changes only an ANDI immediate in one aligned word.
        # Both versions are valid independently, including in a delay slot.
        for address, original in self.sites:
            desired = original if self.count else original & 0xFFFF0000
            if self.pine.read_int32(address) != desired:
                self.pine.write_int32(address, desired)

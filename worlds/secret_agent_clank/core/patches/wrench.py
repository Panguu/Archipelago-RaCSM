import struct

from ...constants import NativeFunctions
from ..symbols import require
from ..batch_io import read_blocks
from .asm import Patch, jump, packed
from .patch import PatchSet

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
        self.ownership_address = None

    def entitlements(self):
        return {name: self.count >= index + 2 for index, name in enumerate(WRENCH_MODS)} if self.enabled else {}

    def prepare(self, symbols, module):
        self.ownership_address = None
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
        addresses = [require(symbols, name) for name, *_ in specs]
        blocks = read_blocks(self.pine, [(address, size) for address, (_, size, *_) in zip(addresses, specs)])
        for address, block, (name, size, prologue, mask, expected) in zip(addresses, blocks, specs):
            code = struct.unpack("<" + "I" * (size // 4), block)
            if code[0] != prologue:
                raise RuntimeError(f"Unrecognized Ratchet wrench gate: {name}")
            sites = [(address + i * 4, word) for i, word in enumerate(code) if word == mask]
            if len(sites) != expected:
                raise RuntimeError(f"Ratchet wrench input layout changed: {name}")
            self.sites.extend(sites)
        self.power_address = require(symbols, "g_wrench_wrenchPower")
        self.patches = [Patch(a, struct.pack("<I", word), struct.pack("<I", word if self.count else word & 0xFFFF0000))
                for a, word in self.sites]
        return self.patches

    def prepare_permanent(self, symbols, module, arena):
        """Compile both input paths; runtime ownership changes only one word.

        Cloning whole functions preserves the ANDI instructions in branch
        delay slots. Internal branches retain their displacement and internal
        direct jumps are rebased. Reject unmodelled escaping branches rather
        than silently generating an unsafe clone.
        """
        enabled, count = self.enabled, self.count
        try:
            self.enabled, self.count = True, 0
            self.prepare(symbols, module)
        finally:
            self.enabled, self.count = enabled, count
        self.patches = []
        if module not in RATCHET_MODULES:
            return []
        self.ownership_address = arena.allocate(bytes(4))
        sites = dict(self.sites)
        specs = ((NativeFunctions.RATCHET_UPDATE_CONTROLS_NORMAL_ACTION_BUTTONS, 0x538),
                 (NativeFunctions.RATCHET_UPDATE_CONTROLS_CROUCH_ACTION_BUTTONS, 0x228),
                 (NativeFunctions.RATCHET_CHECK_JUMP_ATTACK, 0x158))
        for name, size in specs:
            target = require(symbols, name)
            original = self.pine.read_bytes(target, size)
            code = list(struct.unpack("<" + "I" * (size // 4), original))
            clone = (arena.base + arena.cursor + 15) & ~15
            for index, instruction in enumerate(code):
                pc = target + index * 4
                opcode = instruction >> 26
                if opcode in (1, 4, 5, 6, 7, 20, 21, 22, 23) or (
                        opcode == 17 and (instruction >> 21) & 31 == 8):
                    delta = instruction & 65535
                    destination = pc + 4 + (delta - 65536 if delta & 32768 else delta) * 4
                    if not target <= destination < target + size:
                        raise RuntimeError(f"Wrench clone branch escapes {name}")
                elif opcode in (2, 3):
                    destination = ((pc + 4) & 0xF0000000) | ((instruction & 0x3FFFFFF) << 2)
                    if target <= destination < target + size:
                        code[index] = jump(clone + destination - target, opcode == 3)
                elif opcode == 0 and instruction & 63 == 8 and (instruction >> 21) & 31 != 31:
                    raise RuntimeError(f"Wrench clone contains an indirect jump: {name}")
                if pc in sites:
                    code[index] &= 0xFFFF0000
            if arena.allocate(packed(code)) != clone:
                raise RuntimeError("Wrench clone allocation changed")
            tail = arena.allocate(original[:8] + packed([jump(target + 8), 0]))
            flag = self.ownership_address
            dispatcher = arena.allocate(packed([
                0x3C020000 | ((flag + 0x8000) >> 16),
                0x8C420000 | (flag & 65535),
                0x10400003, 0, jump(tail), 0, jump(clone), 0]))
            self.patches.append(Patch(target, original[:8], packed([jump(dispatcher), 0])))
        self.sites = []
        return self.patches

    def sync(self):
        if self.ownership_address is not None:
            module, loading, selected = self.pine.batch_read_int32(
                [0x206328, 0x206324, self.power_address])
            if module != self.module or loading != 0xFFFFFFFF:
                return
            writes = [(self.ownership_address, int(not self.enabled or self.count > 0))]
            if self.enabled and selected > max(0, self.count - 1):
                writes.append((self.power_address, 0))
            self.pine.batch_write_int32(writes)
            return

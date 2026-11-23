import struct

from ...constants import PROGRESSIVE_WRENCH, WRENCH_MOD_ITEMS, NativeFunctions, SACRatchetWrenchWeapons
from ..symbols import require
from ..batch_io import read_blocks
from .asm import Patch, jump, packed
from .patch import PatchSet

WRENCH_MODS = tuple(WRENCH_MOD_ITEMS.values())
RATCHET_MODULES = {3, 9, 14, 21, 25}
# Input handler, its size, its first instruction, the wrench button mask, and
# how many times that mask appears.
INPUT_HANDLERS = (
    (NativeFunctions.RATCHET_UPDATE_CONTROLS_NORMAL_ACTION_BUTTONS, 0x538, 0x27BDFFC0, 0x30A20020, 2),
    (NativeFunctions.RATCHET_UPDATE_CONTROLS_CROUCH_ACTION_BUTTONS, 0x228, 0x27BDFFE0, 0x30420020, 1),
    (NativeFunctions.RATCHET_CHECK_JUMP_ATTACK, 0x158, 0x27BDFFE0, 0x30420020, 1),
)


class WrenchProgression(PatchSet):
    def __init__(self, pine):
        super().__init__(pine)
        self.enabled = False
        self.has_wrench = False
        self.mods = frozenset()
        self.module = None
        self.power_address = None
        self.ownership_address = None

    @property
    def unlocked(self):
        return not self.enabled or self.has_wrench

    def receive(self, names):
        """Progressive copies unlock the wrench then each mod in order; the separate items unlock their own."""
        copies = list(names).count(PROGRESSIVE_WRENCH)
        self.has_wrench = copies > 0 or SACRatchetWrenchWeapons.WRENCH in names
        self.mods = frozenset({*WRENCH_MODS[:max(0, copies - 1)],
                               *(power for item, power in WRENCH_MOD_ITEMS.items() if item in names)})

    def entitlements(self):
        return {name: name in self.mods for name in WRENCH_MODS} if self.enabled else {}

    def prepare(self, symbols, module, arena):
        """Clone each input handler with the wrench masks cleared, and pick the
        clone or the original from one flag word the client sets.

        Whole functions are cloned so masks in delay slots come along. Branches
        must stay inside the function; jumps within it are moved to the clone.
        """
        self.patches = []
        self.module = module
        self.power_address = self.ownership_address = None
        if module not in RATCHET_MODULES:
            return []
        addresses = [require(symbols, name) for name, *_ in INPUT_HANDLERS]
        blocks = read_blocks(self.pine, [(address, size) for address, (_, size, *_) in zip(addresses, INPUT_HANDLERS)])
        self.power_address = require(symbols, "g_wrench_wrenchPower")
        self.ownership_address = arena.allocate(bytes(4))
        for target, original, (name, size, prologue, mask, expected) in zip(addresses, blocks, INPUT_HANDLERS):
            code = list(struct.unpack("<" + "I" * (size // 4), original))
            if code[0] != prologue:
                raise RuntimeError(f"Unrecognized Ratchet wrench gate: {name}")
            if code.count(mask) != expected:
                raise RuntimeError(f"Ratchet wrench input layout changed: {name}")
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
                if instruction == mask:
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
        return self.patches

    def sync(self):
        if self.ownership_address is None:
            return
        module, loading, selected = self.pine.batch_read_int32([0x206328, 0x206324, self.power_address])
        if module != self.module or loading != 0xFFFFFFFF:
            return
        writes = [(self.ownership_address, int(self.unlocked))]
        # Power 0 is the plain wrench; 1-4 are the mods. Drop back to plain if the mod isn't owned.
        if self.enabled and selected and (selected > len(WRENCH_MODS) or WRENCH_MODS[selected - 1] not in self.mods):
            writes.append((self.power_address, 0))
        self.pine.batch_write_int32(writes)

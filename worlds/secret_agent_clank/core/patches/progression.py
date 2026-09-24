"""Native AP weapon tiers and gain multipliers, installed at the loader gate."""
import struct
from collections import Counter

from ...constants.native_functions import NativeFunctions
from ...constants.weapon_progression import PROGRESSIVE_TO_INTERNAL, TITAN_LOCATIONS, max_level
from ..inventories.weapons import WEAPON_ORDER
from ..symbols import require
from .asm import Patch, jump, packed
from .gain_storage import GainStorage
from .patch import PatchSet
from .titan_vendor import TitanPrice


class Progression(PatchSet):
    @staticmethod
    def gain_wrapper(target, original, register, multiplier):
        # Preserve nonpositive adjustments (e.g. deductions). v1 and HI/LO are
        # caller-saved; original prologues below do not consume their old values.
        return packed([0x18000003 | (register << 21), 0x24030000 | multiplier,
                       (register << 21) | (3 << 16) | 0x18,
                       (register << 11) | 0x12,
                       *struct.unpack("<2I", original), jump(target + 8), 0])

    def __init__(self, pine):
        super().__init__(pine)
        self.enabled = False
        self.ng_plus = 0
        self.weapon_xp = self.health_xp = self.bolts = 1
        self.levels = {}
        self.base = None
        self.ng_address = None
        self.save_pointer_address = None
        self.module = None
        self.pending_definitions = ()

    def configure(self, data):
        self.enabled = bool(data.get("progressive_weapons", False))
        self.ng_plus = int(data.get("ng_plus", 0))
        if self.ng_plus not in (0, 1, 2):
            raise ValueError("ng_plus must be between 0 and 2")
        for attr, key in (("weapon_xp", "weapon_xp_multiplier"), ("health_xp", "health_xp_multiplier"), ("bolts", "bolt_multiplier")):
            value = int(data.get(key, 1))
            if not 1 <= value <= 10:
                raise ValueError(f"{key} must be between 1 and 10")
            setattr(self, attr, value)

    def receive(self, names):
        counts = Counter(names)
        self.levels = {internal: min(counts[name], max_level(internal, self.ng_plus))
                       for name, internal in PROGRESSIVE_TO_INTERNAL.items()} if self.enabled else {}

    def ownership(self):
        return {name: level > 0 for name, level in self.levels.items()}

    def prepare(self, symbols, hooks, module, *, vendor_enabled=True):
        self.patches = []
        p = self.pine
        self.ng_address = None
        self.save_pointer_address = None
        self.pending_definitions = ()
        self.module = module
        self.base = symbols.get("GADGET_g_GadgetList")
        replay = require(symbols, NativeFunctions.GLOBALVARS_IS_IN_REPLAY_MODE)
        a, b, c, d = struct.unpack("<4I", p.read_bytes(replay + 0x1C, 16))
        if (a & 0xFFFF0000 != 0x3C020000 or b & 0xFFFF0000 != 0x8C440000
                or c != 0x8C830ED4 or d != 0x0003182B):
            raise RuntimeError("Native NG+ getter changed")
        low = b & 65535
        pointer = ((a & 65535) << 16) + (low - 65536 if low & 32768 else low)
        if pointer % 4 or not 0x100000 <= pointer <= 0x1FFFFFC:
            raise RuntimeError(f"Invalid native save pointer address: 0x{pointer:08X}")
        # The relocated module has not run its initialization at this gate.
        # Validate code now, but dereference initialized data in sync().
        self.save_pointer_address = pointer
        if self.enabled or self.ng_plus:
            if self.base is None:
                raise RuntimeError("Missing native gadget list")
            get = require(symbols, NativeFunctions.GADGET_GET_CURRENT_POWER_LEVEL)
            if p.read_int32(get + 0x20) != 0x8C42005C:
                raise RuntimeError("Weapon level getter layout changed")
            self.pending_definitions = tuple(self.levels if self.enabled else TITAN_LOCATIONS)
        ranges = list(getattr(hooks, "extra_ranges", ()))
        give, buy = symbols.get(NativeFunctions.WEAPON_PICKUP_GIVE_WEAPON), symbols.get(NativeFunctions.SCRNVENDOR_PROCESS_PURCHASE)
        if give is not None:
            ranges.append((give + 0x60, give + 0x278))
        if buy is not None:
            ranges.append((buy + 0x1FC, buy + 0x338))
        edits = []
        if self.enabled or (module == 31 and self.ng_plus):
            xp = require(symbols, NativeFunctions.GADGET_GETS_XP)
            if p.read_bytes(xp, 8) != packed([0x27BDFFB0, 0xFFB30028]):
                raise RuntimeError("Weapon XP entry changed")
            edits.append(Patch(xp, p.read_bytes(xp, 8), packed([0x03E00008, 0x00001021])))
            # AP tiers bypass XP. Treehouse has no combat XP sources and
            # also lends this body to its NG+ vendor hook storage.
            ranges.append((xp + 8, xp + 0x170))
        extra_storage = bool(getattr(hooks, "extra_ranges", ()))
        def allocate(data):
            nonlocal extra_storage
            occupied = [(x.address, x.address + len(x.replacement)) for x in hooks.patches + edits]
            for start, end in ranges:
                for address in range(start, end - len(data) + 1, 4):
                    if all(address + len(data) <= a or address >= b for a, b in occupied):
                        edits.append(Patch(address, p.read_bytes(address, len(data)), data))
                        return address
            if not extra_storage:
                guards, extra_ranges = GainStorage(p).prepare(symbols)
                edits.extend(guards)
                ranges.extend(extra_ranges)
                extra_storage = True
                return allocate(data)
            raise RuntimeError(
                f"Insufficient verified hook storage for gain multipliers "
                f"(module {module}, requested {len(data)} bytes, "
                f"weapon XP {self.weapon_xp}, health XP {self.health_xp}, "
                f"bolts {self.bolts}, NG+ {self.ng_plus}, vendor {vendor_enabled})")
        if self.ng_plus and vendor_enabled:
            edits.extend(TitanPrice(p).prepare(symbols, allocate))
        targets = [(NativeFunctions.PLAYER_GRANT_BOLTS, self.bolts, 4, 0x27BDFFF0, 0xFFB00000)]
        # Treehouse has no combat XP sources. Its small vendor-only arena
        # needs only the bolt handler for any environmental bolt gains.
        if module != 31:
            targets.append((NativeFunctions.GLOBALVARS_ADD_EXPERIENCE, self.health_xp, 4, 0x27BDFFE0, None))
            if not self.enabled:
                targets.append((NativeFunctions.GADGET_GETS_XP, self.weapon_xp, 5, 0x27BDFFB0, 0xFFB30028))
        for name, multiplier, register, first, second in targets:
            if multiplier == 1:
                continue
            target = require(symbols, name)
            original = p.read_bytes(target, 8)
            a, b = struct.unpack("<2I", original)
            if a != first or (b != second if second is not None else b & 0xFFFF0000 != 0x3C020000):
                raise RuntimeError(f"Gain routine changed: {name}")
            address = allocate(self.gain_wrapper(target, original, register, multiplier))
            edits.append(Patch(target, original, packed([jump(address), 0])))
        self.patches = edits
        return edits

    def sync(self):
        if self.base is None:
            return
        if self.module is not None and (self.pine.read_int32(0x206328) != self.module
                or self.pine.read_int32(0x206324) != 0xFFFFFFFF
                or self.pine.read_int32(0x206338) != 3):
            self.ng_address = None
            return
        if self.save_pointer_address is not None:
            self.ng_address = None
            save = self.pine.read_int32(self.save_pointer_address)
            if save == 0:
                return  # Not initialized yet; retry without any progression writes.
            if save % 4 or not 0x100000 <= save < 0x1FE0000:
                raise RuntimeError(f"Invalid native save pointer at 0x{self.save_pointer_address:08X}: 0x{save:08X}")
            self.ng_address = save + 0xED4
        for internal in self.pending_definitions:
            base = self.base + WEAPON_ORDER.index(internal) * 0x74
            defs = struct.unpack("<8I", self.pine.read_bytes(base + 0x10, 32))
            expected = 4 if internal == "ryno" else 8
            if any(not 0x100000 <= a < 0x2000000 for a in defs[:expected]) or any(defs[expected:]):
                raise RuntimeError(f"Unexpected native level definitions for {internal}")
        self.pending_definitions = ()
        writes = []
        if self.ng_address is not None and self.pine.read_int32(self.ng_address) != self.ng_plus:
            writes.append((self.ng_address, self.ng_plus))
        if self.ng_plus and not self.enabled:
            # V4 has no combat path into Titan: normally the vendor supplies
            # V5. AP vendor purchases are checks, so bridge that boundary as
            # soon as an owned weapon reaches V4. Leave V5-V8 XP untouched.
            for internal in TITAN_LOCATIONS:
                base = self.base + WEAPON_ORDER.index(internal) * 0x74
                if self.pine.read_int32(base + 0x70) and self.pine.read_int32(base + 0x5C) == 3:
                    writes.extend(((base + 0x5C, 4), (base + 0x64, 0)))
        for internal, level in self.levels.items():
            base = self.base + WEAPON_ORDER.index(internal) * 0x74
            native = max(0, level - 1)
            current = self.pine.read_int32(base + 0x5C)
            if current != native and (self.enabled or current < native):
                writes.append((base + 0x5C, native))
            if (self.enabled or current < native) and self.pine.read_int32(base + 0x64):
                writes.append((base + 0x64, 0))
        if writes:
            self.pine.batch_write_int32(writes)

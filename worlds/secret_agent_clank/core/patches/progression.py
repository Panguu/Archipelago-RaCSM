"""Native AP weapon tiers and gain multipliers, installed at the loader gate."""
import struct
from bisect import bisect_right
from collections import Counter

from ...constants import CASES_BY_OPERATIVE, SACOperatives
from ...constants.challenge_mode import PROGRESSIVE_CHALLENGE_MODE
from ...constants.nanotech import (
    CLANK_START_NANOTECH,
    CLANK_XP_SAVE_OFFSET,
    CLANK_XP_THRESHOLDS,
    nanotech_levels,
    nanotech_location_name,
)
from ...constants.native_functions import NativeFunctions
from ...constants.native_modules import CASE_MODULES
from ...constants.weapon_progression import (
    LEVELLED_INTERNALS,
    PROGRESSIVE_TO_INTERNAL,
    TITAN_LOCATIONS,
    checked_levels,
    level_location_name,
    max_level,
)
from ..inventories.weapons import WEAPON_ORDER
from ..symbols import require
from .asm import Patch, jump, packed
from .gain_storage import GainStorage
from .mips import A0, RA, T0, T1, T2, V0, ZERO, addiu, addu, beq, jr, lbu, li32, lui, lw, sll, sltiu, sltu
from .patch import PatchSet
from .storage import free_blocks, plan_storage
from .titan_vendor import TitanPrice


class Progression(PatchSet):
    @staticmethod
    def gain_wrapper(target, original, register, multiplier):
        # Preserve nonpositive adjustments (e.g. deductions). v1 and HI/LO are
        # caller-saved; original prologues below do not consume their old values.
        first, second = struct.unpack("<2I", original)
        if multiplier > 0 and multiplier & (multiplier - 1) == 0:
            # The verified stack adjustment is safe on both paths. A shift
            # replaces loading the multiplier and using HI/LO.
            return packed([0x18000002 | (register << 21), first,
                           sll(register, register, multiplier.bit_length() - 1),
                           second, jump(target + 8), 0])
        return packed([0x18000003 | (register << 21), 0x24030000 | multiplier,
                       (register << 21) | (3 << 16) | 0x18,
                       (register << 11) | 0x12,
                       first, jump(target + 8), second])

    def __init__(self, pine):
        super().__init__(pine)
        self.stealth = None
        self.enabled = False
        self.manual = False
        self.check_mode = 0
        self.nanotech_checks_enabled = False
        self.ratchet_nanotech_checks_enabled = False
        self.cap_address = None
        self.ng_plus = 0
        self.max_challenge_mode = 0
        self.progressive_challenge_mode = False
        self.weapon_xp = self.health_xp = self.bolts = 1
        self.levels = {}
        self.base = None
        self.ng_address = None
        self.save_pointer_address = None
        self.module = None
        self.pending_definitions = ()

    def configure(self, data):
        mode = data.get("progressive_weapons", False)
        # Old slot data used a boolean toggle: true always meant automatic.
        mode = (2 if mode else 0) if isinstance(mode, bool) else int(mode)
        if mode not in (0, 1, 2):
            raise ValueError("progressive_weapons must be off, manual, or automatic")
        self.enabled = mode != 0
        self.manual = mode == 1
        self.check_mode = int(data.get("weapon_level_checks", 0))
        if self.check_mode not in range(5):
            raise ValueError("weapon_level_checks must be between 0 and 4")
        self.nanotech_checks_enabled = bool(data.get("nanotech_checks", False))
        self.ratchet_nanotech_checks_enabled = bool(data.get("ratchet_nanotech_checks", False))
        self.max_challenge_mode = int(data.get("ng_plus", 0))
        if self.max_challenge_mode not in (0, 1, 2):
            raise ValueError("ng_plus must be between 0 and 2")
        self.progressive_challenge_mode = bool(data.get("progressive_challenge_mode", False))
        self.ng_plus = 0 if self.progressive_challenge_mode else self.max_challenge_mode
        for attr, key in (("weapon_xp", "weapon_xp_multiplier"), ("health_xp", "health_xp_multiplier"), ("bolts", "bolt_multiplier")):
            value = int(data.get(key, 1))
            if not 1 <= value <= 10:
                raise ValueError(f"{key} must be between 1 and 10")
            setattr(self, attr, value)

    def receive(self, names):
        counts = Counter(names)
        if self.progressive_challenge_mode:
            self.ng_plus = min(counts[PROGRESSIVE_CHALLENGE_MODE], self.max_challenge_mode)
        self.levels = {internal: min(counts[name], max_level(internal, self.ng_plus))
                       for name, internal in PROGRESSIVE_TO_INTERNAL.items()} if self.enabled else {}

    def ownership(self):
        return {name: level > 0 for name, level in self.levels.items()}

    @staticmethod
    def manual_xp_guard(base, caps, tail, allocate):
        """Two small guard blocks fit verified stubs without a 120-byte arena."""
        # Select the native XP tail or the caller return with MOVZ.
        # The shared return delay slot sets the ignored/blocked result to zero.
        continuation = allocate(packed([
                 lui(T1, (base + 0x5C + 0x8000) >> 16), addu(T0, T0, T1),
                 lw(T1, (base + 0x5C) & 0xFFFF, T0),
                 addiu(T1, T1, 1), sltu(T0, T1, T2),
                 *li32(T1, tail), (RA << 21) | (T0 << 16) | (T1 << 11) | 0x0A,
                 jr(T1), addu(V0, ZERO, ZERO)]))
        return packed([sltiu(T0, A0, len(WEAPON_ORDER)), beq(T0, ZERO, 9),
                 *li32(T0, caps), addu(T0, T0, A0), lbu(T2, 0, T0),
                 addiu(T1, ZERO, 0x74),
                 (A0 << 21) | (T1 << 16) | 0x19,  # multu a0,t1
                 (T0 << 11) | 0x12,  # mflo t0; only caller-saved HI/LO change
                 jump(continuation), 0, jr(RA), addu(V0, ZERO, ZERO)])

    def level_checks(self):
        if not self.check_mode or self.base is None:
            return ()
        result = []
        for internal in LEVELLED_INTERNALS:
            base = self.base + WEAPON_ORDER.index(internal) * 0x74
            if not self.pine.read_int32(base + 0x70):
                continue
            level = self.pine.read_int32(base + 0x5C) + 1
            for target in checked_levels(internal, self.check_mode, self.ng_plus):
                if level >= target:
                    result.append(level_location_name(internal, target))
        return result

    def nanotech_checks(self):
        # sync() clears ng_address during transitions or before save initialization.
        if not self.nanotech_checks_enabled or self.ng_address is None:
            return ()
        save = self.ng_address - 0xED4
        xp = self.pine.read_int32(save + CLANK_XP_SAVE_OFFSET)
        if xp > 0x7FFFFFFF:
            return ()
        health = CLANK_START_NANOTECH + bisect_right(CLANK_XP_THRESHOLDS, xp) - 1
        return tuple(nanotech_location_name(level) for level in nanotech_levels(self.ng_plus)
                     if level <= health)

    def ratchet_nanotech_checks(self, symbols):
        if not self.ratchet_nanotech_checks_enabled or self.ng_address is None or not symbols:
            return ()
        from ..ratchet_nanotech import read_ratchet_nanotech
        from ...constants.nanotech import ratchet_nanotech_levels, ratchet_nanotech_location_name
        try:
            data = read_ratchet_nanotech(self.pine, symbols)
        except ValueError:
            return ()  # Loading or invalid data cannot award a location.
        return tuple(ratchet_nanotech_location_name(level)
                     for level in ratchet_nanotech_levels(self.ng_plus)
                     if level <= data['xp_nanotech'])

    def prepare(self, symbols, hooks, module, *, vendor_enabled=True):
        self.patches = []
        p = self.pine
        self.ng_address = None
        self.save_pointer_address = None
        self.pending_definitions = ()
        self.cap_address = None
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
        if self.nanotech_checks_enabled:
            table = require(symbols, "g_LevelProgressionExperienceData_Clank")
            expected = b"".join(struct.pack("<III", index, xp, CLANK_START_NANOTECH + index)
                                for index, xp in enumerate(CLANK_XP_THRESHOLDS))
            if p.read_bytes(table, len(expected)) != expected:
                raise RuntimeError("Clank nanotech progression table changed")
            add_clank = require(symbols, "GLOBALVARS_AddClankExperience__Fi")
            # The dedicated Clank routine loads XP from pGV + 0x18000 + 0x1930.
            for offset, word in ((0x4C, 0x3C030001), (0x54, 0x34638000),
                                 (0x5C, 0x00832021), (0x60, 0x8C821930)):
                if p.read_int32(add_clank + offset) != word:
                    raise RuntimeError("Clank nanotech XP save layout changed")
            if require(symbols, "pGV") != pointer:
                raise RuntimeError("Clank nanotech save pointer changed")
        if self.enabled or self.max_challenge_mode:
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
        if buy is not None and vendor_enabled:
            ranges.append((buy + 0x1FC, buy + 0x338))
        edits = []
        if (self.enabled and not self.manual) or (module == 31 and self.max_challenge_mode):
            xp = require(symbols, NativeFunctions.GADGET_GETS_XP)
            if p.read_bytes(xp, 8) != packed([0x27BDFFB0, 0xFFB30028]):
                raise RuntimeError("Weapon XP entry changed")
            edits.append(Patch(xp, p.read_bytes(xp, 8), packed([0x03E00008, 0x00001021])))
            # AP tiers bypass XP. Treehouse has no combat XP sources and
            # also lends this body to its NG+ vendor hook storage.
            ranges.append((xp + 8, xp + 0x170))
        base_edits = list(edits)

        def build(allocate):
            if vendor_enabled:
                edits.extend(TitanPrice(p).prepare(symbols, allocate))
            if self.manual and module != 31:
                xp = require(symbols, NativeFunctions.GADGET_GETS_XP)
                original = p.read_bytes(xp, 8)
                if original != packed([0x27BDFFB0, 0xFFB30028]):
                    raise RuntimeError("Weapon XP entry changed")
                self.cap_address = allocate(bytes(len(WEAPON_ORDER)))
                tail = (self.gain_wrapper(xp, original, 5, self.weapon_xp)
                        if self.weapon_xp != 1 else original + packed([jump(xp + 8), 0]))
                wrapper = self.manual_xp_guard(self.base, self.cap_address, allocate(tail), allocate)
                address = allocate(wrapper)
                edits.append(Patch(xp, original, packed([jump(address), 0])))
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
            if self.stealth is not None:
                # Shared DLLs can contain Clank code even on another operative's
                # route. Only the Clank success call is intercepted, never generic kills.
                # Clank cases use distinct modules, so the module names the case.
                clank_cases = {CASE_MODULES[case.name]: case.name for case in CASES_BY_OPERATIVE[SACOperatives.CLANK]}
                if module in clank_cases:
                    edits.extend(self.stealth.prepare(symbols, allocate, clank_cases[module]))
                else:
                    self.stealth.binding = None

        # First measure all code and data, including stealth. Placeholder
        # addresses are used only to encode fixed-size instructions; no RAM
        # reads or writes are made through them. Rebuild with final addresses.
        sizes = []
        def measure(data):
            sizes.append(len(data))
            return 0
        build(measure)
        occupied = hooks.patches + edits
        addresses = plan_storage(ranges, occupied, sizes)
        if addresses is None and not getattr(hooks, "gain_storage_prepared", False):
            guards, extra_ranges = GainStorage(p).prepare(symbols)
            base_edits.extend(guards)
            occupied += guards
            ranges.extend(extra_ranges)
            addresses = plan_storage(ranges, occupied, sizes)
        if addresses is None and not vendor_enabled:
            guards, extra_ranges = GainStorage(p).prepare_line(symbols)
            base_edits.extend(guards)
            occupied += guards
            ranges.extend(extra_ranges)
            addresses = plan_storage(ranges, occupied, sizes)
        if addresses is None:
            self.cap_address = None
            if self.stealth is not None:
                self.stealth.binding = None
            available = [end - start for start, end in free_blocks(ranges, occupied)]
            raise RuntimeError(
                f"Insufficient verified storage for complete native hook plan "
                f"(module {module}, requests {sizes}, total {sum(sizes)} bytes; "
                f"free {sum(available)} bytes, largest block {max(available, default=0)} bytes, "
                f"blocks {available})")
        edits = base_edits
        index = 0
        def allocate(data):
            nonlocal index
            if index >= len(sizes) or len(data) != sizes[index]:
                raise RuntimeError("Native hook size changed between planning and encoding")
            address = addresses[index]
            index += 1
            edits.append(Patch(address, p.read_bytes(address, len(data)), data))
            return address
        build(allocate)
        if index != len(sizes):
            raise RuntimeError("Native hook requests changed between planning and encoding")
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
        if self.cap_address is not None:
            caps = bytes(self.levels.get(internal, 0) for internal in WEAPON_ORDER)
            if self.pine.read_bytes(self.cap_address, len(caps)) != caps:
                self.pine.write_bytes(self.cap_address, caps)
        if self.ng_plus and (not self.enabled or self.manual):
            # V4 has no combat path into Titan: normally the vendor supplies
            # V5. AP vendor purchases are checks, so bridge that boundary as
            # soon as an owned weapon reaches V4. Leave V5-V8 XP untouched.
            for internal in TITAN_LOCATIONS:
                if self.manual and self.levels.get(internal, 0) < 5:
                    continue
                base = self.base + WEAPON_ORDER.index(internal) * 0x74
                if self.pine.read_int32(base + 0x70) and self.pine.read_int32(base + 0x5C) == 3:
                    writes.extend(((base + 0x5C, 4), (base + 0x64, 0)))
        for internal, level in self.levels.items():
            base = self.base + WEAPON_ORDER.index(internal) * 0x74
            native = max(0, level - 1)
            current = self.pine.read_int32(base + 0x5C)
            if self.manual:
                # Raise the ceiling, not the earned level. Clamp saves from a
                # previous session and discard XP while frozen at the ceiling.
                if current > native:
                    writes.append((base + 0x5C, native))
                if current >= native and self.pine.read_int32(base + 0x64):
                    writes.append((base + 0x64, 0))
                continue
            if current != native and (self.enabled or current < native):
                writes.append((base + 0x5C, native))
            if (self.enabled or current < native) and self.pine.read_int32(base + 0x64):
                writes.append((base + 0x64, 0))
        if writes:
            self.pine.batch_write_int32(writes)

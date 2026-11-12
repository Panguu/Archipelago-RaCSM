import struct
from collections import Counter

from ...constants import (
    CASES_BY_OPERATIVE,
    CASE_MODULES,
    LEVELLED_INTERNALS,
    PROGRESSIVE_CHALLENGE_MODE,
    PROGRESSIVE_TO_INTERNAL,
    TITAN_LOCATIONS,
    WEAPON_ORDER,
    NativeFunctions,
    ProgressiveWeaponsOptions,
    SACOperatives,
    WeaponLevelChecksOptions,
    checked_levels,
    level_location_name,
    max_level,
    nanotech_levels,
    nanotech_location_name,
    ratchet_nanotech_levels,
    ratchet_nanotech_location_name,
)
from ..nanotech import read_nanotech
from ..symbols import require
from ..batch_io import read_blocks, write_blocks
from .asm import Patch, jump, packed
from .mips import A0, RA, T0, T1, T2, V0, ZERO, addiu, addu, beq, jr, lbu, li32, lui, lw, sltiu, sltu
from .patch import PatchSet
from .titan_vendor import TitanPrice


class Progression(PatchSet):
    def __init__(self, pine):
        super().__init__(pine)
        self.stealth = None
        self.mission_failure = None
        self.enabled = False
        self.manual = False
        self.check_mode = WeaponLevelChecksOptions.OFF
        self.nanotech_checks_enabled = False
        self.ratchet_nanotech_checks_enabled = False
        self.cap_address = None
        self.pickup_challenge_address = None
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
        self.config_address = None

    def configure(self, data):
        mode = int(data.get("progressive_weapons", ProgressiveWeaponsOptions.OFF))
        if mode not in (ProgressiveWeaponsOptions.OFF, ProgressiveWeaponsOptions.MANUAL,
                        ProgressiveWeaponsOptions.AUTOMATIC):
            raise ValueError("progressive_weapons must be off, manual, or automatic")
        self.enabled = mode != ProgressiveWeaponsOptions.OFF
        self.manual = mode == ProgressiveWeaponsOptions.MANUAL
        self.check_mode = int(data.get("weapon_level_checks", WeaponLevelChecksOptions.OFF))
        if self.check_mode not in range(WeaponLevelChecksOptions.OFF, WeaponLevelChecksOptions.ALL + 1):
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

    def level_checks(self):
        if not self.check_mode or self.base is None:
            return ()
        result = []
        bases = [self.base + WEAPON_ORDER.index(internal) * 0x74 for internal in LEVELLED_INTERNALS]
        values = iter(self.pine.batch_read_int32([address for base in bases for address in (base + 0x70, base + 0x5C)]))
        for internal in LEVELLED_INTERNALS:
            owned, level = next(values), next(values) + 1
            if not owned:
                continue
            for target in checked_levels(internal, self.check_mode, self.ng_plus):
                if level >= target:
                    result.append(level_location_name(internal, target))
        return result

    def nanotech_checks(self, symbols):
        if not self.nanotech_checks_enabled or self.ng_address is None or not symbols:
            return ()
        try:
            data = read_nanotech(self.pine, symbols, SACOperatives.CLANK)
        except ValueError:
            return ()  # still loading
        return tuple(nanotech_location_name(level) for level in nanotech_levels(self.ng_plus)
                     if level <= data['xp_nanotech'])

    def ratchet_nanotech_checks(self, symbols):
        if not self.ratchet_nanotech_checks_enabled or self.ng_address is None or not symbols:
            return ()
        try:
            data = read_nanotech(self.pine, symbols, SACOperatives.RATCHET)
        except ValueError:
            return ()  # still loading
        return tuple(ratchet_nanotech_location_name(level) for level in ratchet_nanotech_levels(self.ng_plus)
                     if level <= data['xp_nanotech'])

    def prepare(self, symbols, module, arena, *, vendor_enabled=True):
        p = self.pine
        self.ng_address = None
        self.save_pointer_address = None
        self.pending_definitions = ()
        self.cap_address = None
        self.module = module
        self.config_address = arena.allocate(packed([1, 1, 1]))
        self.base = symbols.get("GADGET_g_GadgetList")
        replay = require(symbols, NativeFunctions.GLOBALVARS_IS_IN_REPLAY_MODE)
        level_getter = symbols.get(NativeFunctions.GADGET_GET_CURRENT_POWER_LEVEL)
        entries = [address for address in (symbols.get(name) for name in (
            NativeFunctions.GADGET_GETS_XP, NativeFunctions.PLAYER_GRANT_BOLTS,
            NativeFunctions.GLOBALVARS_ADD_EXPERIENCE,
            NativeFunctions.GLOBALVARS_ADD_CLANK_EXPERIENCE)) if address is not None]
        getter_code, level_load, *entry_code = read_blocks(p, [
            (replay + 0x1C, 16), (level_getter + 0x20 if level_getter is not None else replay, 4),
            *((address, 8) for address in entries)])
        entry = dict(zip(entries, entry_code))
        a, b, c, d = struct.unpack("<4I", getter_code)
        if (a & 0xFFFF0000 != 0x3C020000 or b & 0xFFFF0000 != 0x8C440000
                or c != 0x8C830ED4 or d != 0x0003182B):
            raise RuntimeError("Native NG+ getter changed")
        low = b & 65535
        pointer = ((a & 65535) << 16) + (low - 65536 if low & 32768 else low)
        if pointer % 4 or not 0x100000 <= pointer <= 0x1FFFFFC:
            raise RuntimeError(f"Invalid native save pointer address: 0x{pointer:08X}")
        # The module hasn't initialised yet, so the pointer is followed in sync().
        self.save_pointer_address = pointer
        if self.enabled or self.max_challenge_mode:
            if self.base is None:
                raise RuntimeError("Missing native gadget list")
            require(symbols, NativeFunctions.GADGET_GET_CURRENT_POWER_LEVEL)
            if level_load != packed([0x8C42005C]):
                raise RuntimeError("Weapon level getter layout changed")
            self.pending_definitions = tuple(self.levels if self.enabled else TITAN_LOCATIONS)

        edits = self.replay_xp_patches(symbols)
        if module == 31 and self.max_challenge_mode:
            # The Treehouse has no combat, so weapon XP is switched off there.
            xp = require(symbols, NativeFunctions.GADGET_GETS_XP)
            if entry[xp] != packed([0x27BDFFB0, 0xFFB30028]):
                raise RuntimeError("Weapon XP entry changed")
            edits.append(Patch(xp, entry[xp], packed([0x03E00008, 0x00001021])))

        # Challenge-only pickups are removed during object init, before sync()
        # has set the save's challenge level, so that one check reads the AP
        # level directly.
        pickup_init = symbols.get("WeaponPickup_Init__FP4Moby")
        if pickup_init is not None:
            pickup_gate = p.read_bytes(pickup_init + 0x38, 24)
            if pickup_gate != packed([0x9042001C, 0x10400007, 0x8E510058,
                                      jump(replay, True), 0, 0x14400004]):
                raise RuntimeError("Challenge pickup initialization gate changed")
            self.pickup_challenge_address = arena.allocate(self.ng_plus.to_bytes(4, "little"))
            flag = self.pickup_challenge_address
            routine = arena.allocate(packed([lui(V0, (flag + 0x8000) >> 16),
                                             lw(V0, flag & 0xFFFF, V0), jr(RA), 0]))
            edits.append(Patch(pickup_init + 0x44, pickup_gate[12:16], packed([jump(routine, True)])))
        else:
            self.pickup_challenge_address = None
        if vendor_enabled:
            edits.extend(TitanPrice(p).prepare(symbols, arena.allocate))

        targets = [(NativeFunctions.PLAYER_GRANT_BOLTS, 0x27BDFFF0, 0xFFB00000)]
        if module != 31:
            xp = require(symbols, NativeFunctions.GADGET_GETS_XP)
            original = entry[xp]
            if original != packed([0x27BDFFB0, 0xFFB30028]):
                raise RuntimeError("Weapon XP entry changed")
            self.cap_address = arena.allocate(bytes(len(WEAPON_ORDER)))
            tail = arena.allocate(original + packed([jump(xp + 8), 0]))
            guard = arena.allocate(self.manual_xp_guard(self.base, self.cap_address, tail, arena.allocate))
            edits.append(Patch(xp, original, packed([jump(guard), 0])))

            targets.append((NativeFunctions.GLOBALVARS_ADD_EXPERIENCE, 0x27BDFFE0, None))
            # Clank's XP goes through its own function, not the player one above.
            if symbols.get(NativeFunctions.GLOBALVARS_ADD_CLANK_EXPERIENCE) is not None:
                targets.append((NativeFunctions.GLOBALVARS_ADD_CLANK_EXPERIENCE, 0x27BDFFF0, 0xFFB00000))
            award = p.read_bytes(xp + 0xFC, 16)
            if award != packed([0x0050182B, 0x0043900B, 0x16A00005, 0x8E840064]):
                raise RuntimeError("Weapon XP award layout changed")
            wrapper = arena.allocate(self.weapon_gain_wrapper(xp, self.config_address))
            edits.append(Patch(xp + 0x104, award[8:], packed([jump(wrapper), 0])))
        for name, first, second in targets:
            target = require(symbols, name)
            original = entry[target]
            a, b = struct.unpack("<2I", original)
            if a != first or (b != second if second is not None else b & 0xFFFF0000 != 0x3C020000):
                raise RuntimeError(f"Gain routine changed: {name}")
            multiplier = self.config_address + (8 if name == NativeFunctions.PLAYER_GRANT_BOLTS else 4)
            wrapper = arena.allocate(self.gain_wrapper(target, original, multiplier))
            edits.append(Patch(target, original, packed([jump(wrapper), 0])))

        if self.stealth is not None:
            # Each Clank case has its own module, so the module tells us the case.
            clank_cases = {CASE_MODULES[case.name]: case.name for case in CASES_BY_OPERATIVE[SACOperatives.CLANK]}
            if module in clank_cases:
                edits.extend(self.stealth.prepare(symbols, arena.allocate, clank_cases[module]))
            else:
                self.stealth.binding = None
        if self.mission_failure is not None:
            edits.extend(self.mission_failure.prepare(symbols, arena.allocate))
        self.patches = edits
        return edits

    def sync(self):
        if self.base is None:
            return
        status = [0x206328, 0x206324, 0x206338]
        if self.save_pointer_address is not None:
            status.append(self.save_pointer_address)
        module, loading, state, *save = self.pine.batch_read_int32(status)
        if self.module is not None and (module != self.module or loading != 0xFFFFFFFF or state != 3):
            self.ng_address = None
            return
        if self.save_pointer_address is not None:
            self.ng_address = None
            save, = save
            if save == 0:
                return  # not initialised yet
            if save % 4 or not 0x100000 <= save < 0x1FE0000:
                raise RuntimeError(f"Invalid native save pointer at 0x{self.save_pointer_address:08X}: 0x{save:08X}")
            self.ng_address = save + 0xED4
        definitions = read_blocks(self.pine, [(self.base + WEAPON_ORDER.index(internal) * 0x74 + 0x10, 32)
                                              for internal in self.pending_definitions])
        for internal, data in zip(self.pending_definitions, definitions):
            defs = struct.unpack("<8I", data)
            expected = 4 if internal == "ryno" else 8
            if any(not 0x100000 <= a < 0x2000000 for a in defs[:expected]) or any(defs[expected:]):
                raise RuntimeError(f"Unexpected native level definitions for {internal}")
        self.pending_definitions = ()
        bridged = []
        if self.ng_plus and (not self.enabled or self.manual):
            # XP can't take a weapon past V4; normally the vendor sells V5.
            # Vendor purchases are checks here, so bump owned V4 weapons to V5.
            bridged = [self.base + WEAPON_ORDER.index(internal) * 0x74 for internal in TITAN_LOCATIONS
                       if not self.manual or self.levels.get(internal, 0) >= 5]
        levelled = [(self.base + WEAPON_ORDER.index(internal) * 0x74, max(0, level - 1))
                    for internal, level in self.levels.items()]
        caps = (bytes((self.levels.get(internal, 0) if self.manual else
                       0 if self.enabled else 255) for internal in WEAPON_ORDER)
                if self.cap_address is not None else b"")
        words = [*((self.ng_address,) if self.ng_address is not None else ()),
                 *((self.pickup_challenge_address,) if self.pickup_challenge_address is not None else ()),
                 *(address for base in bridged for address in (base + 0x70, base + 0x5C)),
                 *(address for base, _ in levelled for address in (base + 0x5C, base + 0x64))]
        *values, current_caps = read_blocks(self.pine, [*((address, 4) for address in words),
                                                        (self.cap_address or 0, len(caps))])
        value = dict(zip(words, (int.from_bytes(data, "little") for data in values)))
        writes = []
        if self.ng_address is not None and value[self.ng_address] != self.ng_plus:
            writes.append((self.ng_address, self.ng_plus))
        if self.pickup_challenge_address is not None and value[self.pickup_challenge_address] != self.ng_plus:
            writes.append((self.pickup_challenge_address, self.ng_plus))
        for base in bridged:
            if value[base + 0x70] and value[base + 0x5C] == 3:
                writes.extend(((base + 0x5C, 4), (base + 0x64, 0)))
        for base, native in levelled:
            current = value[base + 0x5C]
            if self.manual:
                # The AP level is a ceiling, not the level itself. Clamp anything
                # above it and drop XP while the weapon sits at the ceiling.
                if current > native:
                    writes.append((base + 0x5C, native))
                if current >= native and value[base + 0x64]:
                    writes.append((base + 0x64, 0))
                continue
            if current != native and (self.enabled or current < native):
                writes.append((base + 0x5C, native))
            if (self.enabled or current < native) and value[base + 0x64]:
                writes.append((base + 0x64, 0))
        blocks = [(address, data.to_bytes(4, "little")) for address, data in writes]
        if self.config_address is not None:
            blocks.append((self.config_address, packed([self.weapon_xp, self.health_xp, self.bolts])))
        if caps and current_caps != caps:
            blocks.insert(0, (self.cap_address, caps))
        if blocks:
            write_blocks(self.pine, blocks)

    def replay_xp_patches(self, symbols):
        """Keep first-clear XP budgets on repeat challenges and enemy kills."""
        edits = []
        arena = symbols.get("Arena_PreCalcXPForChallenge__FP4Moby")
        if arena is not None:
            code = self.pine.read_bytes(arena + 0x98, 24)
            words = struct.unpack("<6I", code)
            if (words[:3] != (0x3C013F80, 0x4481A000, 0x10400003)
                    or words[3] & 0xFFFF0000 != 0x8E440000
                    or words[4:] != (0x3C013E80, 0x4481A000)):
                raise RuntimeError("Arena repeat XP layout changed")
            # f20 is 1.0 for a first clear, 0.25 after a previous win.
            edits.append(Patch(arena + 0xA8, code[16:20], packed([0x3C013F80])))
        moby = symbols.get("MOBY_ComputeWeaponXP__FPC4MobyRC10DamageInfo")
        if moby is not None:
            code = self.pine.read_bytes(moby + 0x188, 32)
            if code != packed([0x14400005, 0, 0x3C013E80, 0x44810000,
                               0, 0x4600A502, 0x4600A024, 0x44080000]):
                raise RuntimeError("Enemy repeat XP layout changed")
            # Repeat kills normally give a quarter of the XP; make it the full amount.
            edits.append(Patch(moby + 0x190, code[8:12], packed([0x3C013F80])))
        return edits

    @staticmethod
    def manual_xp_guard(base, caps, tail, allocate):
        """Split in two so each half fits in a small free block."""
        # MOVZ picks between the game's XP code and returning straight away.
        # Either way the delay slot returns 0.
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
                 (T0 << 11) | 0x12,  # mflo t0
                 jump(continuation), 0, jr(RA), addu(V0, ZERO, ZERO)])

    @staticmethod
    def gain_wrapper(target, original, config):
        # Multiply a positive a0 by the word at `config`, then run the two
        # displaced instructions and carry on. v1 and HI/LO are free here.
        first, second = struct.unpack("<2I", original)
        return packed([0x18000005 | A0 << 21, 0,
                       0x3C030000 | ((config + 0x8000) >> 16),
                       0x8C630000 | (config & 65535),
                       A0 << 21 | 3 << 16 | 0x18,
                       A0 << 11 | 0x12,
                       first, jump(target + 8), second])

    @staticmethod
    def weapon_gain_wrapper(target, config):
        # s2 holds the award after level scaling and the per-hit cap, so the
        # bonus is applied after the cap. Then replay the bnez s5 and its slot.
        return packed([0x3C030000 | ((config + 0x8000) >> 16),
                       0x8C630000 | (config & 65535), 0x02430019, 0x00009012,
                       0x16A00003, 0x8E840064, jump(target + 0x10C), 0,
                       jump(target + 0x11C), 0])

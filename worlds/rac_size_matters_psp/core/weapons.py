from __future__ import annotations

import struct as _struct
from collections.abc import Callable
from typing import TYPE_CHECKING, NamedTuple

from BaseClasses import ItemClassification

from ..constants import Rac5GadgetKeys, Rac5WeaponKeys
from .locations import weapon_locations as _weapon_locations

if TYPE_CHECKING:
    from ..pypsp import Psp

# Vendor/mod location lookups live in core.locations.weapon_locations, not
# here — that module builds them lazily on first use to avoid an import
# cycle (items.py imports this module's weapon constants directly, and
# top-level locations.py imports both core.weapons siblings and items.py).


WEAPON_STRUCT_SIZE = 0x58
WEAPON_MIN_CONSECUTIVE = 4

# ProgressiveWeapons option values (options.py's ProgressiveWeapons Choice)
# — kept in sync manually with the raw-int slot_data values.
PROGRESSIVE_OFF       = 0
PROGRESSIVE_MANUAL    = 1
PROGRESSIVE_AUTOMATIC = 2

class WeaponData(NamedTuple):
    is_projectile: bool
    classification: ItemClassification
    max_level: int
    mod_count: int
    # Experience required to reach each level, 1-indexed (exp_thresholds[0]
    # is the experience needed for level 2, etc. — level 1 needs none).
    # Length is always max_level - 1.
    exp_thresholds: tuple[int, ...] = ()


# Single source of truth per weapon (keyed by internal Rac5WeaponKeys).
# WEAPON_MAX_LEVELS/WEAPON_MOD_COUNTS/WEAPON_EXP_THRESHOLDS below are derived
# from this; items.py and rules/_helpers.py derive projectile/classification
# membership from it too.
WEAPON_DATA: dict[str, WeaponData] = {
    Rac5WeaponKeys.LACERATOR: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=4, mod_count=2,
        exp_thresholds=(3000, 9000, 15000),
    ),
    Rac5WeaponKeys.CONCUSSION_GUN: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=4, mod_count=3,
        exp_thresholds=(6000, 9000, 12000),
    ),
    Rac5WeaponKeys.ACID_BOMB_GLOVE: WeaponData(
        is_projectile=False, classification=ItemClassification.progression, max_level=4, mod_count=2,
        exp_thresholds=(3000, 6000, 9000),
    ),
    Rac5WeaponKeys.AGENTS_OF_DOOM: WeaponData(
        is_projectile=False, classification=ItemClassification.progression, max_level=4, mod_count=2,
        exp_thresholds=(6000, 9000, 12000),
    ),
    Rac5WeaponKeys.BEE_MINE_GLOVE: WeaponData(
        is_projectile=False, classification=ItemClassification.progression, max_level=4, mod_count=2,
        exp_thresholds=(6000, 7500, 9000),
    ),
    Rac5WeaponKeys.STATIC_BARRIER: WeaponData(
        is_projectile=False, classification=ItemClassification.useful, max_level=4, mod_count=2,
        exp_thresholds=(15000, 18000, 21000),
    ),
    Rac5WeaponKeys.SHOCK_ROCKET: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=4, mod_count=3,
        exp_thresholds=(15000, 19000, 42000),
    ),
    Rac5WeaponKeys.SNIPER_MINE: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=4, mod_count=2,
        exp_thresholds=(4000, 5500, 7000),
    ),
    Rac5WeaponKeys.SCORCHER: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=4, mod_count=2,
        exp_thresholds=(7000, 8500, 10000),
    ),
    Rac5WeaponKeys.LASER_TRACER: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=4, mod_count=2,
        exp_thresholds=(15000, 27000, 45000),
    ),
    Rac5WeaponKeys.SUCK_CANNON: WeaponData(
        is_projectile=True, classification=ItemClassification.useful, max_level=4, mod_count=0,
        exp_thresholds=(3500, 5000, 7000),
    ),
    Rac5WeaponKeys.MOOTATOR: WeaponData(
        is_projectile=False, classification=ItemClassification.progression, max_level=4, mod_count=0,
        exp_thresholds=(12000, 12000, 16000),
    ),
    Rac5WeaponKeys.RYNO: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=4, mod_count=0,
        exp_thresholds=(85000, 350000, 999000),
    ),
}

WEAPON_MOD_COUNTS: dict[str, int] = {key: data.mod_count for key, data in WEAPON_DATA.items()}

WEAPON_MAX_LEVELS: dict[str, int] = {key: data.max_level for key, data in WEAPON_DATA.items()}

# Per-weapon tuple of fixed experience thresholds, 1-indexed by level reached
# (see WeaponData.exp_thresholds) — placeholder zeros until real values are
# supplied.
WEAPON_EXP_THRESHOLDS: dict[str, tuple[int, ...]] = {
    key: data.exp_thresholds for key, data in WEAPON_DATA.items()
}


def exp_threshold_for_level(weapon: str, level: int) -> int | None:
    """Fixed experience value required to reach `level` (1-indexed) for
    `weapon`, or None if there's no threshold for that level (level 1, or
    out of range)."""
    thresholds = WEAPON_EXP_THRESHOLDS.get(weapon, ())
    idx = level - 2
    if idx < 0 or idx >= len(thresholds):
        return None
    return thresholds[idx]


def is_weapon_candidate(data: bytes, i: int) -> bool:
    if i + 0x46 > len(data):
        return False
    if data[i + 0x3D] > 1 or data[i + 0x3E] > 1 or data[i + 0x3F] > 1:
        return False
    if data[i + 0x45] > 1:
        return False
    level, = _struct.unpack_from("<I", data, i + 0x2D)
    if level > 7:
        return False
    ammo, = _struct.unpack_from("<I", data, i + 0x31)
    if ammo > 9999:
        return False
    icon, = _struct.unpack_from("<I", data, i + 0x1D)
    if icon == 0:
        return False
    return True


def is_ps2_weapon_candidate(data: bytes, i: int) -> bool:
    if i + 0x46 > len(data):
        return False
    if data[i + 0x3D] > 1 or data[i + 0x3E] > 1 or data[i + 0x3F] > 1:
        return False
    if data[i + 0x45] > 1:
        return False
    level, = _struct.unpack_from("<I", data, i + 0x2D)
    if level > 7:
        return False
    ammo, = _struct.unpack_from("<I", data, i + 0x31)
    if ammo > 9999:
        return False
    icon, = _struct.unpack_from("<I", data, i + 0x1D)
    if icon == 0:
        return False
    item, = _struct.unpack_from("<I", data, i + 0x15)
    if item == 0:
        return False
    return True


class WeaponByteField:
    """Psp-backed accessor for a single-byte weapon struct field
    (unlocked, mod_slot_N, mod_unlock_N)."""

    def __init__(self, field_name: str) -> None:
        self.field_name = field_name

    def _address(self, instance) -> int:
        return instance.base + instance._OFFSETS[self.field_name]

    def __get__(self, instance, owner) -> bool | None:
        if instance is None:
            return None
        return bool(instance.pine.read_int8(self._address(instance)))

    def __set__(self, instance, value: bool) -> None:
        if instance is None:
            return
        instance.pine.write_int8(self._address(instance), int(value))

    def __delete__(self, instance) -> None:
        if instance is None:
            return
        instance.pine.write_int8(self._address(instance), 0)


class WeaponInt32Field:
    """Psp-backed accessor for a single int32 weapon struct field."""

    def __init__(self, field_name: str) -> None:
        self.field_name = field_name

    def _address(self, instance) -> int:
        return instance.base + instance._OFFSETS[self.field_name]

    def __get__(self, instance, owner) -> int | None:
        if instance is None:
            return None
        return instance.pine.read_int32(self._address(instance))

    def __set__(self, instance, value: int) -> None:
        if instance is None:
            return
        instance.pine.write_int32(self._address(instance), value)

    def __delete__(self, instance) -> None:
        if instance is None:
            return
        instance.pine.write_int32(self._address(instance), 0)


class WeaponAddresses:
    """Psp-backed live accessor for one weapon struct instance, replacing
    the old plain address-holder class — every field reads/writes memory
    directly via its descriptor instead of callers manually poking
    self.pine.read_int8(addr.field)."""

    _OFFSETS: dict[str, int] = {
        "level":            0x2D,
        # Confirmed in-game for Lacerator on Pokitaru; same relative offset for every weapon.
        "experience":       0x35,
        "mod_slot_one":     0x3D,
        "mod_slot_two":     0x3E,
        "mod_slot_three":   0x3F,
        "mod_unlock_one":   0x40,
        "mod_unlock_two":   0x41,
        "mod_unlock_three": 0x42,
        "unlocked":         0x45,
    }

    level            = WeaponInt32Field("level")
    experience       = WeaponInt32Field("experience")
    mod_slot_one     = WeaponByteField("mod_slot_one")
    mod_slot_two     = WeaponByteField("mod_slot_two")
    mod_slot_three   = WeaponByteField("mod_slot_three")
    mod_unlock_one   = WeaponByteField("mod_unlock_one")
    mod_unlock_two   = WeaponByteField("mod_unlock_two")
    mod_unlock_three = WeaponByteField("mod_unlock_three")
    unlocked         = WeaponByteField("unlocked")

    def __init__(self, base: int, pine: Psp) -> None:
        self.base = base
        self.pine = pine

    def __repr__(self) -> str:
        return f"WeaponAddresses(base=0x{self.base:08X}, unlocked={self.unlocked}, level={self.level})"


class GadgetAddresses:
    """Psp-backed live accessor for one gadget struct instance."""

    _OFFSETS: dict[str, int] = {
        "unlocked": 0x45,
    }

    unlocked = WeaponByteField("unlocked")

    def __init__(self, base: int, pine: Psp) -> None:
        self.base = base
        self.pine = pine

    def __repr__(self) -> str:
        return f"GadgetAddresses(base=0x{self.base:08X}, unlocked={self.unlocked})"


class GadgetData(NamedTuple):
    classification: ItemClassification


# Single source of truth per gadget (keyed by internal Rac5GadgetKeys).
# Gadgets have no level/mod/projectile concept, so classification is the
# only flag needed.
GADGET_DATA: dict[str, GadgetData] = {
    Rac5GadgetKeys.HYPERSHOT:      GadgetData(classification=ItemClassification.progression),
    Rac5GadgetKeys.SPROUT_O_MATIC: GadgetData(classification=ItemClassification.progression),
    Rac5GadgetKeys.POLARIZER:      GadgetData(classification=ItemClassification.progression),
    Rac5GadgetKeys.PDA:            GadgetData(classification=ItemClassification.useful),
    Rac5GadgetKeys.SHRINK_RAY:     GadgetData(classification=ItemClassification.progression),
    Rac5GadgetKeys.BOLT_GRABBER:   GadgetData(classification=ItemClassification.useful),
    Rac5GadgetKeys.MAP_O_MATIC:    GadgetData(classification=ItemClassification.useful),
    Rac5GadgetKeys.BOX_BREAKER:    GadgetData(classification=ItemClassification.useful),
}


WEAPON_ORDER: list[str | None] = [
    Rac5WeaponKeys.LACERATOR,        # slot  0
    Rac5WeaponKeys.CONCUSSION_GUN,   # slot  1
    Rac5WeaponKeys.ACID_BOMB_GLOVE,  # slot  2
    Rac5WeaponKeys.AGENTS_OF_DOOM,   # slot  3
    Rac5WeaponKeys.BEE_MINE_GLOVE,   # slot  4
    Rac5WeaponKeys.STATIC_BARRIER,   # slot  5
    Rac5WeaponKeys.SHOCK_ROCKET,     # slot  6
    Rac5WeaponKeys.SNIPER_MINE,      # slot  7
    Rac5WeaponKeys.SCORCHER,         # slot  8
    Rac5WeaponKeys.LASER_TRACER,     # slot  9
    Rac5WeaponKeys.SUCK_CANNON,      # slot 10
    Rac5WeaponKeys.MOOTATOR,         # slot 11
    None,
    Rac5WeaponKeys.RYNO,             # slot 12 
]

GADGET_ORDER: list[str | None] = [
    Rac5GadgetKeys.HYPERSHOT,        # slot 0
    Rac5GadgetKeys.SPROUT_O_MATIC,   # slot 1
    Rac5GadgetKeys.POLARIZER,        # slot 2
    Rac5GadgetKeys.PDA,              # slot 3
    Rac5GadgetKeys.SHRINK_RAY,       # slot 4
    Rac5GadgetKeys.BOLT_GRABBER,     # slot 5
    None,                            # slot 6  gap
    Rac5GadgetKeys.MAP_O_MATIC,      # slot 7
    Rac5GadgetKeys.BOX_BREAKER,      # slot 8
]


def build_weapons(array_base: int | None, pine: Psp) -> tuple[dict[str, WeaponAddresses], dict[str, GadgetAddresses]]:
    if array_base is None:
        return {}, {}

    weapons: dict[str, WeaponAddresses] = {}
    for i, name in enumerate(WEAPON_ORDER):
        if name is not None:
            weapons[name] = WeaponAddresses(array_base + i * WEAPON_STRUCT_SIZE, pine)

    gadget_base = array_base + len(WEAPON_ORDER) * WEAPON_STRUCT_SIZE
    gadgets: dict[str, GadgetAddresses] = {}
    for i, name in enumerate(GADGET_ORDER):
        if name is not None:
            gadgets[name] = GadgetAddresses(gadget_base + i * WEAPON_STRUCT_SIZE, pine)

    return weapons, gadgets


# Weapon state (runtime)

_MOD_SLOTS = ("mod_slot_one", "mod_slot_two", "mod_slot_three")


class WeaponInventory:
    """Psp-backed live accessor + ownership/vendor tracking for weapons,
    gadgets and mods.

    Planet-dependent: the weapon/gadget array lives at a per-planet base
    address, so call set_base(array_base) whenever the loaded planet changes.
    check() just reports what changed since the last call.
    """

    def __init__(self, pine: Psp) -> None:
        self.pine = pine
        _weapon_locations._ensure_loc_data()
        # Base of the current planet's weapon+gadget array, set alongside
        # self._weapon_addrs/_gadget_addrs by set_base() — used for one bulk
        # read_bytes() call spanning every struct instead of ~5-9 individual
        # reads per struct. PPSSPP's debugger protocol is one JSON round-trip
        # per read/write, and this runs every tick, so a single tick could
        # otherwise issue 70+ round trips for weapons alone, enough to
        # visibly stutter the emulator.
        self._array_base: int | None = None
        self.weapons: dict[str, bool]         = {}
        self.gadgets: dict[str, bool]         = {}
        self.mods: dict[str, dict[str, bool]] = {}
        # Raw-memory baselines used only for check()'s "did this just flip
        # 0->1" detection — kept separate from weapons/gadgets/mods above,
        # which never regress True->False. Without this split, a weapon
        # already owned via an AP item received before its vendor location
        # was bought would never be detectable as "just purchased": these
        # baselines track the memory bit itself, so a real purchase flipping
        # memory back to 1 is seen as a fresh transition regardless of prior
        # ownership.
        self._raw_weapons: dict[str, bool]         = {}
        self._raw_gadgets: dict[str, bool]         = {}
        self._raw_mods: dict[str, dict[str, bool]] = {}
        # Last-seen 0-indexed level per weapon, used only for check()'s
        # "newly reached level" diffing.
        self._raw_level: dict[str, int] = {}
        self.vendor_locations: dict[str, bool] = dict.fromkeys(
            (
                *_weapon_locations.VENDOR_WEAPON_LOC,
                *_weapon_locations.VENDOR_GADGET_LOC,
                *_weapon_locations._MOD_LOC,
            ),
            False,
        )
        self._weapon_addrs: dict[str, WeaponAddresses] = {}
        self._gadget_addrs: dict[str, GadgetAddresses] = {}

        # Weapon-experience-multiplier option: 1 = no boost (default/off).
        # Set directly by the client from slot_data.
        self.experience_multiplier: int = 1
        # Last-seen raw experience per weapon, used to diff this tick's gain
        # from the last one — see apply_experience_boost().
        self._prev_experience: dict[str, int] = {}

        # ProgressiveWeapons option (options.py): 0=off, 1=manual, 2=automatic.
        self.progressive_mode: int = PROGRESSIVE_OFF
        # Per-weapon max allowed level (0-indexed, same scale as addr.level),
        # derived from Progressive Weapon copies received; kept current by
        # Core.apply_inventory(). Absent = zero copies, fully locked.
        self.level_caps: dict[str, int] = {}
        # manual mode only, weapons with zero copies received (cap < 0): the
        # experience value to keep rewriting so a fully-locked weapon's
        # experience never moves — captured on first observation, cleared
        # once a first copy arrives. See apply_progressive_leveling().
        self._pinned_experience: dict[str, int] = {}

    def set_base(self, array_base: int | None) -> None:
        """Rebind every weapon/gadget address to the given planet's array
        base, or unbind entirely (every check()/sync() becomes a no-op)
        when array_base is None (unrecognized planet)."""
        self._array_base = array_base
        self._weapon_addrs, self._gadget_addrs = build_weapons(array_base, self.pine)

    def _read_array(self) -> bytes | None:
        """One read_bytes() call spanning every weapon+gadget struct for the
        current planet, or None if no planet array is bound. Callers index
        into the result at i * WEAPON_STRUCT_SIZE + field_offset, matching
        WeaponAddresses/GadgetAddresses._OFFSETS."""
        if self._array_base is None:
            return None
        total_structs = len(WEAPON_ORDER) + len(GADGET_ORDER)
        return self.pine.read_bytes(self._array_base, total_structs * WEAPON_STRUCT_SIZE)

    def get(self, name: str) -> bool:
        addr = self._weapon_addrs.get(name) or self._gadget_addrs.get(name)
        if addr is None:
            return False
        return bool(addr.unlocked)

    def set(self, name: str, value: bool) -> None:
        addr = self._weapon_addrs.get(name) or self._gadget_addrs.get(name)
        if addr is not None:
            addr.unlocked = value

    def delete(self, name: str) -> None:
        self.set(name, False)

    def get_mod(self, weapon: str, slot: str) -> bool:
        addr = self._weapon_addrs.get(weapon)
        if addr is None:
            return False
        return bool(getattr(addr, slot))

    def set_mod(self, weapon: str, slot: str, value: bool) -> None:
        addr = self._weapon_addrs.get(weapon)
        if addr is not None:
            setattr(addr, slot, value)

    def delete_mod(self, weapon: str, slot: str) -> None:
        self.set_mod(weapon, slot, False)

    def get_experience(self, weapon: str) -> int:
        addr = self._weapon_addrs.get(weapon)
        if addr is None:
            return 0
        return addr.experience

    def set_experience(self, weapon: str, value: int) -> None:
        addr = self._weapon_addrs.get(weapon)
        if addr is not None:
            addr.experience = value

    def get_level(self, weapon: str) -> int:
        addr = self._weapon_addrs.get(weapon)
        if addr is None:
            return 0
        return addr.level

    def set_level(self, weapon: str, level: int) -> None:
        addr = self._weapon_addrs.get(weapon)
        if addr is not None:
            addr.level = level

    def zero_levels_for_vendor(self, purchasable: frozenset[str] | None = None) -> dict[str, int]:
        """Snapshot every weapon's current level, then zero out only the
        ones in `purchasable` (every weapon, if not given).

        The weapons vendor's displayed price derives from the weapon's level
        field, so an already-leveled-but-not-yet-AP-owned weapon would
        show/charge a different price than the base one while browsing.
        `purchasable` should be the set of weapons AP does NOT yet own (see
        VendorInventory's callers). Caller passes the returned snapshot to
        restore_levels() once the vendor closes — this method never restores
        on its own.
        """
        snapshot = {name: addr.level for name, addr in self._weapon_addrs.items()}
        for name, addr in self._weapon_addrs.items():
            if purchasable is None or name in purchasable:
                addr.level = 0
        return snapshot

    def restore_levels(self, snapshot: dict[str, int]) -> None:
        """Write back a snapshot taken by zero_levels_for_vendor()."""
        for name, level in snapshot.items():
            addr = self._weapon_addrs.get(name)
            if addr is not None:
                addr.level = level

    def get_mod_unlock(self, weapon: str, attr: str) -> bool:
        addr = self._weapon_addrs.get(weapon)
        if addr is None:
            return False
        return bool(getattr(addr, attr))

    def set_mod_unlock(self, weapon: str, attr: str, value: bool) -> None:
        """Write the mod_unlock_N "purchasable" byte — separate from set_mod
        (does the player *own* the mod): this just controls whether the mod
        vendor shows that slot as buyable."""
        addr = self._weapon_addrs.get(weapon)
        if addr is not None:
            setattr(addr, attr, value)

    def check(self) -> dict[str, list]:
        """Read every weapon/gadget/mod byte for the current planet's array,
        update ownership state, and return what newly changed this call:
        {"weapons": [...], "gadgets": [...], "mods": [(weapon, slot), ...],
        "levels": [(weapon, level), ...]}.

        "Newly changed" is decided from the raw memory bit's own previous
        reading (_raw_weapons/_raw_gadgets/_raw_mods), not from
        weapons/gadgets/mods — those never regress True->False, so diffing
        against them directly would miss a genuine repurchase/re-force of
        something already marked owned. weapons/gadgets/mods themselves
        still only ever go False->True here, preserving "once owned, stays
        owned" for callers like has_weapon()/has_gadget()/has_mod().

        "levels" reports every 1-indexed level >= 2 newly reached since the
        last call, for unlocked weapons — if level jumped by more than one
        step at once, every level in between is reported, not just the
        final one. Level 1 is never reported (synonymous with owning the weapon).
        """
        newly_weapons: list[str] = []
        newly_gadgets: list[str] = []
        newly_mods: list[tuple[str, str]] = []
        newly_levels: list[tuple[str, int]] = []

        data = self._read_array()
        if data is None:
            return {"weapons": [], "gadgets": [], "mods": [], "levels": []}

        for name, addr in self._weapon_addrs.items():
            i = addr.base - self._array_base
            is_unlocked = bool(data[i + addr._OFFSETS["unlocked"]])
            was_unlocked = self._raw_weapons.get(name, False)
            self._raw_weapons[name] = is_unlocked
            if is_unlocked:
                self.weapons[name] = True
            if is_unlocked and not was_unlocked:
                newly_weapons.append(name)
            prev_mods = dict(self._raw_mods.get(name, dict.fromkeys(_MOD_SLOTS, False)))
            raw_mods  = self._raw_mods.setdefault(name, dict.fromkeys(_MOD_SLOTS, False))
            mods      = self.mods.setdefault(name, dict.fromkeys(_MOD_SLOTS, False))
            for slot in _MOD_SLOTS:
                slot_unlocked = bool(data[i + addr._OFFSETS[slot]])
                raw_mods[slot] = slot_unlocked
                if slot_unlocked:
                    mods[slot] = True
                if slot_unlocked and not prev_mods.get(slot, False):
                    newly_mods.append((name, slot))

            if is_unlocked:
                prev_level = self._raw_level.get(name, -1)
                current_level, = _struct.unpack_from("<i", data, i + addr._OFFSETS["level"])
                # Raw memory can transiently read garbage here (the array
                # being rewritten mid-planet-transition): an unbounded
                # current_level would blow the range() below into a
                # multi-billion-iteration loop, freezing the client. A
                # weapon's level can never legitimately exceed its own max,
                # so clamp against that instead of trusting the raw read.
                current_level = min(current_level, WEAPON_MAX_LEVELS.get(name, current_level))
                if current_level > prev_level:
                    for idx in range(prev_level + 1, current_level + 1):
                        level = idx + 1
                        if level >= 2:
                            newly_levels.append((name, level))
                self._raw_level[name] = current_level

        for name, addr in self._gadget_addrs.items():
            i = addr.base - self._array_base
            is_unlocked = bool(data[i + addr._OFFSETS["unlocked"]])
            was_unlocked = self._raw_gadgets.get(name, False)
            self._raw_gadgets[name] = is_unlocked
            if is_unlocked:
                self.gadgets[name] = True
            if is_unlocked and not was_unlocked:
                newly_gadgets.append(name)

        return {
            "weapons": newly_weapons, "gadgets": newly_gadgets,
            "mods": newly_mods, "levels": newly_levels,
        }

    def rebaseline_levels(self) -> None:
        """Reset _raw_level's "last-seen level" baseline for every currently-
        unlocked weapon to match the just-loaded planet's own array, without
        treating the jump from the old baseline as newly-reached levels.

        Call once, right when a planet transition finishes, before check()
        runs normally later that same tick. Each planet holds its own
        separate weapon-level copy, and unlike ownership, level is never
        force-resynced from AP truth every tick — so a freshly-active
        planet's saved level for an already-unlocked weapon can legitimately
        differ from whatever _raw_level tracked on the previous planet, with
        nothing correcting that mismatch. Diffing against the stale baseline
        normally would read every level in between as "just reached this
        tick" and flood a location send per weapon on every transition.

        Deliberately touches _raw_level only — _raw_weapons/_raw_gadgets/
        _raw_mods are left alone, so check()'s normal diffing of those still
        sees the real transition (needed by _suppress_forced_starter_items()
        and vendor-purchase detection).
        """
        data = self._read_array()
        if data is None:
            return
        for name, addr in self._weapon_addrs.items():
            i = addr.base - self._array_base
            if not bool(data[i + addr._OFFSETS["unlocked"]]):
                continue
            current_level, = _struct.unpack_from("<i", data, i + addr._OFFSETS["level"])
            self._raw_level[name] = min(current_level, WEAPON_MAX_LEVELS.get(name, current_level))

    def apply_experience_boost(self) -> None:
        """Inflate each weapon's experience gain by experience_multiplier,
        every tick, so leveling happens faster without touching the game's
        own level-up thresholds.

        Diffed against the raw value last seen here (_prev_experience) so
        only genuine in-game gain since the last tick gets amplified, never
        our own previous write. Stops once a weapon reaches level 4 —
        vanilla's cap for anything using this experience curve
        (Mootator/Ryno don't use it at all, so this is a no-op for them).
        """
        multiplier = self.experience_multiplier
        data = self._read_array()
        if data is None:
            return
        for name, addr in self._weapon_addrs.items():
            i = addr.base - self._array_base
            current, = _struct.unpack_from("<i", data, i + addr._OFFSETS["experience"])
            previous = self._prev_experience.get(name)
            if previous is None:
                self._prev_experience[name] = current
                continue
            diff = current - previous
            if diff <= 0:
                self._prev_experience[name] = current
                continue
            level, = _struct.unpack_from("<i", data, i + addr._OFFSETS["level"])
            if multiplier > 1 and level < 4:
                boosted = previous + diff * multiplier
                addr.experience = boosted
                self._prev_experience[name] = boosted
            else:
                self._prev_experience[name] = current

    def apply_progressive_leveling(self) -> None:
        """Gate weapon leveling behind Progressive Weapon items received,
        every tick. No-op when progressive_mode is PROGRESSIVE_OFF.

        automatic: level is fully dictated by level_caps — pinned to the
        received count, experience zeroed continuously.

        manual: the player levels up by playing normally, but only within
        the window AP has opened. A weapon with no cap yet is fully locked —
        experience is captured on first observation and rewritten every tick
        until a first copy arrives. Below cap, experience is capped every
        tick at the fixed WEAPON_EXP_THRESHOLDS ceiling for the next
        not-yet-permitted level — every tick, not just once level reaches
        cap, because apply_experience_boost() runs first and can, under a
        high multiplier, inflate a single tick's gain past the ceiling in
        one jump, letting the game's leveling logic skip past a level it
        wasn't supposed to reach yet.

        The instant level reaches cap, the game resets experience to 0 —
        it's locked there, not at the ceiling, so organic play can't rack up
        "practice" progress toward an unopened level. Receiving another
        Progressive copy raises cap, lifting the 0-lock and the ceiling
        together.
        """
        mode = self.progressive_mode
        if mode == PROGRESSIVE_OFF:
            return

        data = self._read_array()
        if data is None:
            return

        for name, addr in self._weapon_addrs.items():
            i = addr.base - self._array_base
            level, = _struct.unpack_from("<i", data, i + addr._OFFSETS["level"])
            experience, = _struct.unpack_from("<i", data, i + addr._OFFSETS["experience"])
            cap = self.level_caps.get(name, -1)

            if mode == PROGRESSIVE_AUTOMATIC:
                target_level = max(cap, 0)
                # Only write what's out of place — avoids a steady stream of
                # no-op writes once a weapon is already pinned at its cap.
                if level != target_level:
                    addr.level = target_level
                if experience != 0:
                    addr.experience = 0
                continue

            # manual
            if cap < 0:
                # No Progressive copies received yet — fully locked.
                pinned = self._pinned_experience.get(name)
                if pinned is None:
                    self._pinned_experience[name] = experience
                elif experience != pinned:
                    addr.experience = pinned
                continue
            self._pinned_experience.pop(name, None)

            if level > cap:
                # Shouldn't normally happen (caps only rise), but pull back
                # down defensively rather than leave it over-leveled.
                addr.level = cap
                level = cap

            max_level_idx = WEAPON_MAX_LEVELS.get(name, cap + 1) - 1
            if cap >= max_level_idx:
                continue

            if level == cap:
                # Already at the max permitted level — keep experience at 0
                # (the game's own level-up already did this) rather than
                # letting it climb toward a ceiling with no level to reach.
                if experience != 0:
                    addr.experience = 0
                continue

            # level < cap: room to grow naturally, but never let a single
            # boosted tick's gain carry past the ceiling for the next
            # not-yet-permitted level (cap + 1, same 0-indexing as addr.level).
            ceiling = exp_threshold_for_level(name, cap + 1)
            if ceiling is not None and experience > ceiling:
                addr.experience = ceiling

    def wipe(self) -> None:
        """Zero every weapon/gadget/mod unlock bit, level and experience in
        memory for the current planet's array, and rebaseline every
        tracking dict to match.

        Called once, the first time a planet becomes ready after a fresh
        connect/reconnect (see Core.tick()) — otherwise whatever's sitting
        in the save (vanilla progress, a stale session) would be misread as
        a batch of brand-new pickups the instant check() first runs, since
        every raw baseline starts blank/-1. Core.apply_inventory() writes
        true AP ownership onto this clean state afterward via sync_slots(),
        not check(), so it never reports a spurious change.
        """
        for addr in self._weapon_addrs.values():
            addr.unlocked = False
            for slot in _MOD_SLOTS:
                setattr(addr, slot, False)
            addr.level = 0
            addr.experience = 0
        for addr in self._gadget_addrs.values():
            addr.unlocked = False

        self.weapons = dict.fromkeys(self._weapon_addrs, False)
        self.gadgets = dict.fromkeys(self._gadget_addrs, False)
        self.mods = {name: dict.fromkeys(_MOD_SLOTS, False) for name in self._weapon_addrs}
        self._raw_weapons = dict(self.weapons)
        self._raw_gadgets = dict(self.gadgets)
        self._raw_mods = {name: dict(mods) for name, mods in self.mods.items()}
        self._raw_level = dict.fromkeys(self._weapon_addrs, 0)
        self._prev_experience = dict.fromkeys(self._weapon_addrs, 0)

    def sync(self) -> None:
        """Write the current ownership dicts into game memory for the current planet's array."""
        for name, addr in self._weapon_addrs.items():
            addr.unlocked = self.weapons.get(name, False)
            mods = self.mods.get(name, {})
            for slot in _MOD_SLOTS:
                setattr(addr, slot, mods.get(slot, False))
        for name, addr in self._gadget_addrs.items():
            addr.unlocked = self.gadgets.get(name, False)

    def sync_slots(self) -> None:
        """Read the current planet's array into the ownership dicts (does not
        report changes). Also re-baselines the raw-memory dicts check() diffs
        against, so the next check() call doesn't see this resync's own
        writes as a fresh change."""
        for name, addr in self._weapon_addrs.items():
            unlocked = bool(addr.unlocked)
            self.weapons[name]     = unlocked
            self._raw_weapons[name] = unlocked
            mods     = self.mods.setdefault(name, dict.fromkeys(_MOD_SLOTS, False))
            raw_mods = self._raw_mods.setdefault(name, dict.fromkeys(_MOD_SLOTS, False))
            for slot in _MOD_SLOTS:
                slot_unlocked  = bool(getattr(addr, slot))
                mods[slot]     = slot_unlocked
                raw_mods[slot] = slot_unlocked
            # A fresh planet's array is a separate working copy — rebaseline
            # so apply_experience_boost() doesn't mistake its current value
            # for a same-tick gain relative to the previous planet's array.
            self._prev_experience[name] = addr.experience
            # _raw_level is deliberately NOT rebaselined here — check() only
            # fires on an *increase*, so a stale reading from an unsynced
            # planet array just re-baselines downward with no false fire,
            # while a precollected weapon still correctly fires every level
            # up to its target the first time it's observed (compared
            # against the default "never observed"). Rebaselining here would
            # permanently swallow that first observation.
        for name, addr in self._gadget_addrs.items():
            unlocked = bool(addr.unlocked)
            self.gadgets[name]      = unlocked
            self._raw_gadgets[name] = unlocked

    def apply_vendor_locations(self, allowed_extra: frozenset[str] = frozenset()) -> None:
        """Zero all weapon/gadget/mod memory then restore what the player may keep.

        Weapons/gadgets restored if purchased from vendor (and still owned) OR
        if name is in allowed_extra (owned weapon whose vendor planet is
        unlocked). Mods restored only if purchased from this vendor — owning
        the mod via an AP item received elsewhere does not restore it here.
        """
        weapon_unlocked = dict.fromkeys(self._weapon_addrs, False)
        weapon_mods: dict[str, dict[str, bool]] = {
            name: dict.fromkeys(_MOD_SLOTS, False) for name in self._weapon_addrs
        }
        gadget_unlocked = dict.fromkeys(self._gadget_addrs, False)

        for loc_name, purchased in self.vendor_locations.items():
            if not purchased:
                continue
            if loc_name in _weapon_locations.VENDOR_WEAPON_LOC:
                name = _weapon_locations.VENDOR_WEAPON_LOC[loc_name]
                if self.weapons.get(name, False) and name in weapon_unlocked:
                    weapon_unlocked[name] = True
            elif loc_name in _weapon_locations.VENDOR_GADGET_LOC:
                name = _weapon_locations.VENDOR_GADGET_LOC[loc_name]
                if self.gadgets.get(name, False) and name in gadget_unlocked:
                    gadget_unlocked[name] = True
            elif loc_name in _weapon_locations._MOD_LOC:
                weapon, slot = _weapon_locations._MOD_LOC[loc_name]
                if weapon in weapon_mods:
                    weapon_mods[weapon][slot] = True

        # Weapons/gadgets owned via AP items whose vendor planet is unlocked.
        for name in allowed_extra:
            if name in weapon_unlocked:
                weapon_unlocked[name] = True
            if name in gadget_unlocked:
                gadget_unlocked[name] = True

        for name, addr in self._weapon_addrs.items():
            addr.unlocked = weapon_unlocked[name]
            for slot in _MOD_SLOTS:
                setattr(addr, slot, weapon_mods[name][slot])
        for name, addr in self._gadget_addrs.items():
            addr.unlocked = gadget_unlocked[name]

    def zero_unpurchased_mod_slots(self, names: frozenset[str]) -> None:
        """Re-zero mod_slot_N for the given weapons unless that slot was
        actually bought from this vendor. apply_vendor_locations already
        does this as part of its zero/restore pass, but a Progressive-item
        grant can race back in afterwards — this dedicated second pass
        guarantees the mod vendor shows it as purchasable, not owned."""
        purchased_slots = {
            _weapon_locations._MOD_LOC[loc] for loc, bought in self.vendor_locations.items()
            if bought and loc in _weapon_locations._MOD_LOC
        }
        for name in names:
            addr = self._weapon_addrs.get(name)
            if addr is None:
                continue
            for slot in _MOD_SLOTS:
                if (name, slot) in purchased_slots:
                    continue
                # Read first — skip the write unless something actually set
                # it back to 1 since our last pass (this runs every tick).
                if getattr(addr, slot):
                    setattr(addr, slot, False)

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        for loc in checked_locations:
            if loc in self.vendor_locations:
                self.vendor_locations[loc] = True
            if loc in _weapon_locations.VENDOR_WEAPON_LOC:
                self.weapons[_weapon_locations.VENDOR_WEAPON_LOC[loc]] = True
            elif loc in _weapon_locations.VENDOR_GADGET_LOC:
                self.gadgets[_weapon_locations.VENDOR_GADGET_LOC[loc]] = True
            elif loc in _weapon_locations._MOD_LOC:
                weapon, slot = _weapon_locations._MOD_LOC[loc]
                self.mods.setdefault(weapon, dict.fromkeys(_MOD_SLOTS, False))
                self.mods[weapon][slot] = True

    def level_experience_snapshot(self) -> dict[str, list[int]]:
        """Current [level, experience] per weapon on the currently-bound
        planet's array — for persisting to AP data storage so real leveling
        progress survives a reconnect. wipe() zeroes this data on the first
        planet-ready of a session; without a persisted copy to restore from,
        that wipe would permanently erase real progress instead of just
        resetting the diff baseline.

        Lists, not tuples — round-trips through JSON (AP data storage),
        which has no tuple type.
        """
        return {name: [addr.level, addr.experience] for name, addr in self._weapon_addrs.items()}

    def restore_level_experience(self, data: dict) -> None:
        """Write back a level_experience_snapshot() previously persisted to
        AP data storage — the counterpart to wipe() zeroing this data on the
        first planet-ready of a fresh connect/reconnect. Also rebaselines
        _raw_level/_prev_experience so check() doesn't misread this restore
        as a fresh level-up/experience gain."""
        for name, pair in data.items():
            addr = self._weapon_addrs.get(name)
            if addr is None or not isinstance(pair, (list, tuple)) or len(pair) != 2:
                continue
            level, experience = int(pair[0]), int(pair[1])
            addr.level = level
            addr.experience = experience
            self._raw_level[name] = level
            self._prev_experience[name] = experience

    def revert_unowned(self, is_ap_owned: Callable[[str], bool]) -> None:
        """Zero unlocked + every mod slot (memory and tracking dicts alike)
        for every weapon is_ap_owned says no to.

        Used by the mod vendor to clean up its own temporary "show as
        unlocked so it renders in the selection list" display hack once
        that menu closes. apply_inventory()'s resync is additive only, so
        nothing else would undo that hack — the weapon has to stay visually
        unlocked for the whole visit (or it wouldn't render at all), so it
        can't be re-locked the instant it's observed.
        """
        for weapon, addr in self._weapon_addrs.items():
            if is_ap_owned(weapon):
                continue
            addr.unlocked = False
            self.weapons[weapon] = False
            mods = self.mods.setdefault(weapon, dict.fromkeys(_MOD_SLOTS, False))
            for slot in _MOD_SLOTS:
                setattr(addr, slot, False)
                mods[slot] = False

    def has_weapon(self, name: str) -> bool:
        return self.weapons.get(name, False)

    def has_gadget(self, name: str) -> bool:
        return self.gadgets.get(name, False)

    def has_mod(self, weapon: str, slot: str) -> bool:
        return self.mods.get(weapon, {}).get(slot, False)

    def __repr__(self) -> str:
        unlocked_w = [n for n, v in self.weapons.items() if v]
        unlocked_g = [n for n, v in self.gadgets.items() if v]
        return f"WeaponInventory(weapons={unlocked_w}, gadgets={unlocked_g})"

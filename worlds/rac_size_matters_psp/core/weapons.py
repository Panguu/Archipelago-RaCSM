from __future__ import annotations

import struct as _struct
from collections.abc import Callable
from typing import TYPE_CHECKING, NamedTuple

from BaseClasses import ItemClassification

from ..constants import Rac5GadgetKeys, Rac5WeaponKeys
from .locations import weapon_locations as _weapon_locations

if TYPE_CHECKING:
    from ..pypsp import Psp

# Vendor/mod location lookups (VENDOR_WEAPON_LOC, MOD_UNLOCK_PLANET, etc.)
# live in core.locations.weapon_locations, not here — that module builds them
# lazily on first use since ``items.py`` imports this module's weapon
# constants directly, and top-level ``locations.py`` imports ``core.weapons``
# siblings + items.py, which would otherwise cycle back into this module.


WEAPON_STRUCT_SIZE = 0x58
WEAPON_MIN_CONSECUTIVE = 4

# ProgressiveWeapons option values (options.py's ProgressiveWeapons Choice
# — kept in sync manually, same as the raw-int slot_data comparisons used
# elsewhere in this codebase, e.g. context.py's clank_mode/skill_points).
PROGRESSIVE_OFF       = 0
PROGRESSIVE_MANUAL    = 1
PROGRESSIVE_AUTOMATIC = 2

class WeaponData(NamedTuple):
    is_projectile: bool
    classification: ItemClassification
    max_level: int
    mod_count: int


# Single source of truth per weapon (keyed by internal Rac5WeaponKeys).
# WEAPON_MAX_LEVELS/WEAPON_MOD_COUNTS below are derived from this for
# existing consumers (client/vendor.py, core/vendor.py); items.py and
# rules/_helpers.py derive projectile/classification membership from it too.
WEAPON_DATA: dict[str, WeaponData] = {
    Rac5WeaponKeys.LACERATOR: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=4, mod_count=2,
    ),
    Rac5WeaponKeys.CONCUSSION_GUN: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=4, mod_count=3,
    ),
    Rac5WeaponKeys.ACID_BOMB_GLOVE: WeaponData(
        is_projectile=False, classification=ItemClassification.progression, max_level=4, mod_count=2,
    ),
    Rac5WeaponKeys.AGENTS_OF_DOOM: WeaponData(
        is_projectile=False, classification=ItemClassification.progression, max_level=4, mod_count=2,
    ),
    Rac5WeaponKeys.BEE_MINE_GLOVE: WeaponData(
        is_projectile=False, classification=ItemClassification.progression, max_level=4, mod_count=2,
    ),
    Rac5WeaponKeys.STATIC_BARRIER: WeaponData(
        is_projectile=False, classification=ItemClassification.useful, max_level=4, mod_count=2,
    ),
    Rac5WeaponKeys.SHOCK_ROCKET: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=4, mod_count=3,
    ),
    Rac5WeaponKeys.SNIPER_MINE: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=4, mod_count=2,
    ),
    Rac5WeaponKeys.SCORCHER: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=4, mod_count=2,
    ),
    Rac5WeaponKeys.LASER_TRACER: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=4, mod_count=2,
    ),
    Rac5WeaponKeys.SUCK_CANNON: WeaponData(
        is_projectile=True, classification=ItemClassification.useful, max_level=4, mod_count=0,
    ),
    Rac5WeaponKeys.MOOTATOR: WeaponData(
        is_projectile=False, classification=ItemClassification.progression, max_level=4, mod_count=0,
    ),
    Rac5WeaponKeys.RYNO: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=4, mod_count=0,
    ),
}

WEAPON_MOD_COUNTS: dict[str, int] = {key: data.mod_count for key, data in WEAPON_DATA.items()}

WEAPON_MAX_LEVELS: dict[str, int] = {key: data.max_level for key, data in WEAPON_DATA.items()}


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
        # Confirmed in-game for Lacerator on Pokitaru (0x20F3EA4C, base
        # 0x20F3EA17) — same relative offset for every weapon.
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
# only flag needed — items.py derives GADGET_ITEM_TABLE's classification
# from this instead of keeping its own frozenset.
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
    gadgets and mods, replacing WeaponState.

    Planet-dependent: the weapon/gadget array lives at a per-planet base
    address, so call set_base(array_base) whenever the loaded planet changes
    (array_base comes from WEAPON_ARRAY_BASE_BY_PLANET). Acquire/lose events
    are an external concern now — check() just reports what changed since the
    last call, same shape as ChallengeInventory.check().
    """

    def __init__(self, pine: Psp) -> None:
        self.pine = pine
        _weapon_locations._ensure_loc_data()
        # Base of the current planet's weapon+gadget array (== the address of
        # weapon slot 0), set alongside self._weapon_addrs/_gadget_addrs by
        # set_base() — used to do one bulk read_bytes() call spanning every
        # weapon+gadget struct instead of ~5-9 individual reads per struct.
        # PPSSPP's debugger protocol is one JSON round-trip per read/write
        # call, and check()/apply_experience_boost()/apply_progressive_
        # leveling() each ran every single tick, so this mattered a lot —
        # without it, a single tick could issue 70+ round trips for weapons
        # alone, which was enough to visibly stutter the emulator.
        self._array_base: int | None = None
        self.weapons: dict[str, bool]         = {}
        self.gadgets: dict[str, bool]         = {}
        self.mods: dict[str, dict[str, bool]] = {}
        # Raw-memory baselines used only for check()'s "did this just flip
        # 0->1" detection — kept separate from weapons/gadgets/mods above,
        # which never regress True->False (see check()'s docstring). Without
        # this split, a weapon already owned via an AP item received before
        # its vendor location was ever bought would never be detectable as
        # "just purchased": apply_vendor_locations() zeroes the memory bit for
        # display, but the ownership dict stays True, so a real purchase
        # flipping memory back to 1 would look like no change at all. These
        # baselines track the memory bit itself, so they correctly go back to
        # False whenever apply_vendor_locations() zeroes it, and a genuine
        # purchase is seen as a fresh transition regardless of prior ownership.
        self._raw_weapons: dict[str, bool]         = {}
        self._raw_gadgets: dict[str, bool]         = {}
        self._raw_mods: dict[str, dict[str, bool]] = {}
        # Last-seen 0-indexed level per weapon, used only for check()'s
        # "newly reached level" diffing — separate from level_caps/pinning
        # bookkeeping below, same "raw memory, not derived state" role as
        # _raw_weapons.
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
        # Set directly by the client from slot_data, same pattern as Core's
        # clank_enabled/skill_points_enabled flags.
        self.experience_multiplier: int = 1
        # Last-seen raw experience per weapon, used only to diff this tick's
        # gain from the last one — see apply_experience_boost().
        self._prev_experience: dict[str, int] = {}

        # ProgressiveWeapons option (options.py): 0=off, 1=manual, 2=automatic.
        # Set directly by the client from slot_data.
        self.progressive_mode: int = PROGRESSIVE_OFF
        # Per-weapon max allowed level (0-indexed, same scale as addr.level),
        # derived from how many Progressive Weapon copies AP has granted —
        # kept current by Core.apply_inventory() every time it runs. A
        # weapon absent from this dict has received zero copies (still
        # fully locked, no leveling of any kind allowed).
        self.level_caps: dict[str, int] = {}
        # manual mode only: the experience value to keep rewriting once a
        # weapon is pinned (either not-yet-unlocked, or sitting right at its
        # current cap) — captured the moment it first got pinned, cleared
        # the moment its cap rises again. See apply_progressive_leveling().
        self._pinned_experience: dict[str, int] = {}
        self._prev_level_cap: dict[str, int] = {}

    def set_base(self, array_base: int | None) -> None:
        """Rebind every weapon/gadget address to the given planet's array
        base, or unbind entirely (empty dicts, every check()/sync() call
        becomes a no-op) when array_base is None — an unrecognized planet
        with no known array location, so nothing here should keep pointing
        at whatever the previously loaded planet's array happened to be."""
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

        The weapons vendor's displayed price apparently derives from the
        weapon's level field, so an already-leveled-but-not-yet-AP-owned
        weapon would show/charge a different price than the base one while
        browsing. AP-owned weapons have nothing to hide behind a fake base
        price — real level is kept visible for them even in this view, so
        `purchasable` should be the set of weapons AP does NOT yet own
        (see VendorInventory's callers). Caller holds onto the returned
        snapshot and passes it to restore_levels() once the vendor closes
        (or the view switches) — this method never restores on its own.
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
        weapons/gadgets/mods — those never regress True->False (see
        apply_vendor_locations()), so diffing against them directly would
        miss a genuine repurchase/re-force of something already marked owned.
        weapons/gadgets/mods themselves still only ever go False->True here,
        preserving that "once owned, stays owned" contract for callers like
        has_weapon()/has_gadget()/has_mod().

        "levels" reports every 1-indexed level >= 2 newly reached since the
        last call, for weapons that are actually unlocked — if level jumped
        by more than one step at once (e.g. automatic progressive mode
        setting level straight to a freshly-raised cap), every level in
        between is reported too, not just the final one, so none of their
        locations get silently skipped. Level 1 is never reported here — it
        isn't a location at all (synonymous with owning the weapon), only
        levels 2+ are.
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
                if current_level > prev_level:
                    # Level 1 is deliberately excluded here — it isn't a
                    # location (synonymous with owning the weapon), so only
                    # levels 2+ are ever reported.
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

    def apply_experience_boost(self) -> None:
        """Inflate each weapon's experience gain by experience_multiplier,
        every tick, so leveling happens faster without touching the game's
        own level-up thresholds.

        Diffed against the raw value last seen here (_prev_experience) — the
        same "compare to last raw reading" approach check() uses for
        unlocked bits — so only genuine in-game gain since the last tick
        gets amplified, never our own previous write. A same-or-lower
        reading (no gain yet, or the game reset the counter on a level-up)
        just re-baselines without writing anything.

        Stops entirely once a weapon reaches level 4 — vanilla's normal cap
        for anything that levels via this experience curve (Mootator/Ryno
        don't use it at all, so this is a no-op for them regardless).
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
        every tick. No-op when progressive_mode is PROGRESSIVE_OFF (vanilla
        leveling, untouched).

        automatic: level is fully dictated by level_caps — pinned straight
        to the received count, experience zeroed continuously, so no
        organic play can ever push a level past what's been received.

        manual: the player levels up by playing normally, but only within
        the window AP has actually opened. A weapon with no cap yet (zero
        Progressive copies received) is fully locked — its experience is
        captured the first time it's observed and rewritten every tick
        after, going nowhere until the first copy arrives. Once unlocked,
        experience is left alone (and can freely rise) as long as
        addr.level is still under its cap; the instant it reaches the cap,
        that tick's experience value is captured and rewritten every tick
        after — freezing progress right at the level-up boundary the game
        itself just wrote, rather than resetting to zero. Receiving another
        Progressive copy raises the cap, which clears the pin and lets
        natural play resume until the new cap.
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
                # Only write what's actually out of place — this runs every
                # tick for every weapon, so an unconditional write here was
                # a steady stream of no-op writes even once a weapon's
                # already pinned at its cap.
                if level != target_level:
                    addr.level = target_level
                if experience != 0:
                    addr.experience = 0
                continue

            # manual
            prev_cap = self._prev_level_cap.get(name, -1)
            if cap > prev_cap:
                self._pinned_experience.pop(name, None)
            self._prev_level_cap[name] = cap

            if cap < 0:
                # No Progressive copies received yet — fully locked.
                pinned = self._pinned_experience.get(name)
                if pinned is None:
                    self._pinned_experience[name] = experience
                elif experience != pinned:
                    addr.experience = pinned
                continue

            if level > cap:
                # Shouldn't normally happen (caps only rise), but pull back
                # down defensively rather than leave it over-leveled.
                addr.level = cap
                level = cap

            if level < cap:
                # Room to grow naturally — leave experience alone.
                continue

            # level == cap: freeze right here.
            pinned = self._pinned_experience.get(name)
            if pinned is None:
                self._pinned_experience[name] = experience
            elif experience != pinned:
                addr.experience = pinned

    def wipe(self) -> None:
        """Zero every weapon/gadget/mod unlock bit, level and experience in
        memory for the current planet's array, and rebaseline every
        tracking dict (weapons/gadgets/mods and their _raw_* counterparts,
        plus _raw_level/_prev_experience) to match.

        Called once, the very first time a planet becomes ready after a
        fresh connect/reconnect (see Core.tick()) — before that point,
        whatever's sitting in the save (vanilla progress, a stale prior
        session, anything not actually tracked by AP) would otherwise be
        misread as a batch of brand-new pickups/level-ups the instant
        check() ever runs against it, since every raw baseline starts
        blank/-1. Wiping first means check()'s very first real diff is
        against a clean all-False/level-0 state, so only what
        Core.apply_inventory() writes afterward (true AP ownership) can
        ever look like a change — and that path uses sync_slots(), not
        check(), so it never reports one anyway.
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
            # for a same-tick gain (or a reset) relative to whatever the
            # previous planet's array happened to hold.
            self._prev_experience[name] = addr.experience
            # _raw_level is deliberately NOT rebaselined here (unlike
            # experience above) — check() only ever fires on an *increase*
            # over the last-seen value, so a lower/stale reading from an
            # unsynced planet array just silently re-baselines downward with
            # no false "reached level" fire, and a starting/precollected
            # weapon that's already at its target level the very first time
            # it's ever observed still correctly fires every level up to it
            # (comparing against the untouched default of "never observed").
            # Rebaselining here would instead permanently swallow that first
            # observation, since apply_progressive_leveling() (which would
            # otherwise raise the level to trigger a fresh diff) runs on its
            # own separate tick schedule, not synchronously within this call.
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
                # Guard: only restore if player actually owns it (edge-case safety).
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
        """Explicitly re-zero mod_slot_N for the given weapons unless that
        specific slot was actually bought from this vendor. apply_vendor_locations
        already does this as part of its zero/restore pass, but a Progressive-
        item grant (mod_slot_N=1, owned outright, unrelated to this vendor) can
        still race back in afterwards — calling this right after as a dedicated
        second pass guarantees the mod vendor shows it as purchasable rather
        than already-owned."""
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
                # Read first — this runs every poll tick while the mod vendor
                # is open, so skip the write unless something actually set it
                # back to 1 since our last pass.
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
        """Current [level, experience] per weapon on whichever planet's
        array is currently bound — for persisting to AP data storage (see
        client/context.py's weapon-state Set/Get) so real leveling progress
        (organic play, not something any AP item records) survives a
        reconnect. wipe() below zeroes this same data every session's first
        planet-ready to stop stale/pre-AP memory from being misread as a
        batch of fresh level-ups; without a persisted copy to restore from
        afterward, that wipe would permanently erase real progress instead
        of just resetting the diff baseline it's meant to.

        Lists, not tuples — this round-trips through JSON (AP data storage),
        which has no tuple type; using lists on both ends keeps a later
        equality diff (skip an unnecessary Set) meaningful.
        """
        return {name: [addr.level, addr.experience] for name, addr in self._weapon_addrs.items()}

    def restore_level_experience(self, data: dict) -> None:
        """Write back a level_experience_snapshot() previously persisted to
        AP data storage — the counterpart to wipe() zeroing this same data
        on the first planet-ready of a fresh connect/reconnect. Also
        rebaselines _raw_level/_prev_experience so check()'s next call
        doesn't misread this restore as a fresh level-up/experience gain."""
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
        unlocked so it actually renders in the selection list" display
        hack once that menu closes. apply_inventory()'s resync is additive
        only (it never clears anything not owned), so nothing else would
        ever undo that hack on its own — a vendor purchase only ever
        checks a location, same principle as weapon_vendor()'s re-lock;
        this is that same principle applied on a delay, since the weapon
        has to stay visually unlocked for the whole mod-vendor visit or it
        wouldn't render as a selection at all, so it can't be re-locked the
        instant it's observed the way a real weapon-vendor purchase is.
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

from __future__ import annotations

import struct as _struct
from typing import TYPE_CHECKING, NamedTuple

from BaseClasses import ItemClassification

from ..constants import Rac5GadgetKeys, Rac5WeaponKeys
from .locations import weapon_locations as _weapon_locations

if TYPE_CHECKING:
    from ..pypine import Pine

# Vendor/mod location lookups (VENDOR_WEAPON_LOC, MOD_UNLOCK_PLANET, etc.)
# live in core.locations.weapon_locations, not here — that module builds them
# lazily on first use since ``items.py`` imports this module's weapon
# constants directly, and top-level ``locations.py`` imports ``core.weapons``
# siblings + items.py, which would otherwise cycle back into this module.


# Weapon data

WEAPON_STRUCT_SIZE = 0x58
WEAPON_MIN_CONSECUTIVE = 4

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
        is_projectile=False, classification=ItemClassification.progression, max_level=1, mod_count=0,
    ),
    Rac5WeaponKeys.RYNO: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=5, mod_count=0,
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
    """Pine-backed accessor for a single-byte weapon struct field
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


class WeaponLevelField:
    """Pine-backed accessor for a weapon's level (int32)."""

    def _address(self, instance) -> int:
        return instance.base + instance._OFFSETS["level"]

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
    """Pine-backed live accessor for one weapon struct instance, replacing
    the old plain address-holder class — every field reads/writes memory
    directly via its descriptor instead of callers manually poking
    self.pine.read_int8(addr.field)."""

    _OFFSETS: dict[str, int] = {
        "level":            0x2D,
        "mod_slot_one":     0x3D,
        "mod_slot_two":     0x3E,
        "mod_slot_three":   0x3F,
        "mod_unlock_one":   0x40,
        "mod_unlock_two":   0x41,
        "mod_unlock_three": 0x42,
        "unlocked":         0x45,
    }

    level            = WeaponLevelField()
    mod_slot_one     = WeaponByteField("mod_slot_one")
    mod_slot_two     = WeaponByteField("mod_slot_two")
    mod_slot_three   = WeaponByteField("mod_slot_three")
    mod_unlock_one   = WeaponByteField("mod_unlock_one")
    mod_unlock_two   = WeaponByteField("mod_unlock_two")
    mod_unlock_three = WeaponByteField("mod_unlock_three")
    unlocked         = WeaponByteField("unlocked")

    def __init__(self, base: int, pine: Pine) -> None:
        self.base = base
        self.pine = pine

    def __repr__(self) -> str:
        return f"WeaponAddresses(base=0x{self.base:08X}, unlocked={self.unlocked}, level={self.level})"


class GadgetAddresses:
    """Pine-backed live accessor for one gadget struct instance."""

    _OFFSETS: dict[str, int] = {
        "unlocked": 0x45,
    }

    unlocked = WeaponByteField("unlocked")

    def __init__(self, base: int, pine: Pine) -> None:
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
    None,                            # slot 12  gap
    Rac5WeaponKeys.RYNO,             # slot 13
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


def build_weapons(array_base: int, pine: Pine) -> tuple[dict[str, WeaponAddresses], dict[str, GadgetAddresses]]:
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
    """Pine-backed live accessor + ownership/vendor tracking for weapons,
    gadgets and mods, replacing WeaponState.

    Planet-dependent: the weapon/gadget array lives at a per-planet base
    address, so call set_base(array_base) whenever the loaded planet changes
    (array_base comes from WEAPON_ARRAY_BASE_BY_PLANET). Acquire/lose events
    are an external concern now — check() just reports what changed since the
    last call, same shape as ChallengeInventory.check().
    """

    def __init__(self, pine: Pine) -> None:
        self.pine = pine
        _weapon_locations._ensure_loc_data()
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

    def set_base(self, array_base: int) -> None:
        """Rebind every weapon/gadget address to the given planet's array base."""
        self._weapon_addrs, self._gadget_addrs = build_weapons(array_base, self.pine)

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

    def get_level(self, weapon: str) -> int:
        addr = self._weapon_addrs.get(weapon)
        if addr is None:
            return 0
        return addr.level

    def set_level(self, weapon: str, level: int) -> None:
        addr = self._weapon_addrs.get(weapon)
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
        {"weapons": [...], "gadgets": [...], "mods": [(weapon, slot), ...]}.

        "Newly changed" is decided from the raw memory bit's own previous
        reading (_raw_weapons/_raw_gadgets/_raw_mods), not from
        weapons/gadgets/mods — those never regress True->False (see
        apply_vendor_locations()), so diffing against them directly would
        miss a genuine repurchase/re-force of something already marked owned.
        weapons/gadgets/mods themselves still only ever go False->True here,
        preserving that "once owned, stays owned" contract for callers like
        has_weapon()/has_gadget()/has_mod().
        """
        newly_weapons: list[str] = []
        newly_gadgets: list[str] = []
        newly_mods: list[tuple[str, str]] = []

        for name, addr in self._weapon_addrs.items():
            was_unlocked = self._raw_weapons.get(name, False)
            is_unlocked  = bool(addr.unlocked)
            self._raw_weapons[name] = is_unlocked
            if is_unlocked:
                self.weapons[name] = True
            if is_unlocked and not was_unlocked:
                newly_weapons.append(name)
            prev_mods = dict(self._raw_mods.get(name, dict.fromkeys(_MOD_SLOTS, False)))
            raw_mods  = self._raw_mods.setdefault(name, dict.fromkeys(_MOD_SLOTS, False))
            mods      = self.mods.setdefault(name, dict.fromkeys(_MOD_SLOTS, False))
            for slot in _MOD_SLOTS:
                slot_unlocked = bool(getattr(addr, slot))
                raw_mods[slot] = slot_unlocked
                if slot_unlocked:
                    mods[slot] = True
                if slot_unlocked and not prev_mods.get(slot, False):
                    newly_mods.append((name, slot))

        for name, addr in self._gadget_addrs.items():
            was_unlocked = self._raw_gadgets.get(name, False)
            is_unlocked  = bool(addr.unlocked)
            self._raw_gadgets[name] = is_unlocked
            if is_unlocked:
                self.gadgets[name] = True
            if is_unlocked and not was_unlocked:
                newly_gadgets.append(name)

        return {"weapons": newly_weapons, "gadgets": newly_gadgets, "mods": newly_mods}

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

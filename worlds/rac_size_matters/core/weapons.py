from __future__ import annotations

import struct as _struct
from collections.abc import Callable
from typing import NamedTuple

from BaseClasses import ItemClassification

from ..constants import Rac5GadgetKeys, Rac5WeaponKeys
from ..interface_orchestrator.memory.accessor import MemoryAccessor
from ..interface_orchestrator.state.base_state import BaseState
from ..interface_orchestrator.storage.local import LocalStorage
from ..interface_orchestrator.structs.address_map import AddressMap
from .structs.pickups import GadgetStruct, WeaponStruct

# NOTE: ``..items`` and ``..locations`` are imported lazily (see _ensure_loc_data
# below).  Importing them at module top would create a circular import, because
# ``items.py`` imports this module's weapon constants directly, and
# ``locations.py`` imports ``core.weapons`` siblings + items.py.


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


class WeaponAddresses:
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

    _BYTE_FIELDS: frozenset[str] = frozenset({
        "mod_slot_one", "mod_slot_two", "mod_slot_three",
        "mod_unlock_one", "mod_unlock_two", "mod_unlock_three",
        "unlocked",
    })

    def __init__(self, base: int) -> None:
        self.base = base
        for name, offset in self._OFFSETS.items():
            setattr(self, name, base + offset)

    def fields(self) -> list[str]:
        return list(self._OFFSETS)

    def is_byte(self, field: str) -> bool:
        return field in self._BYTE_FIELDS

    def __repr__(self) -> str:
        fields = "\n".join(
            f"  {name} = 0x{getattr(self, name):08X}"
            for name in self._OFFSETS
        )
        return f"WeaponAddresses(base=0x{self.base:08X})\n{fields}"


class GadgetAddresses:
    _OFFSETS: dict[str, int] = {
        "icon":     0x1D,
        "unlocked": 0x45,
    }

    _BYTE_FIELDS: frozenset[str] = frozenset({"unlocked"})

    def __init__(self, base: int) -> None:
        self.base = base
        for name, offset in self._OFFSETS.items():
            setattr(self, name, base + offset)

    def fields(self) -> list[str]:
        return list(self._OFFSETS)

    def is_byte(self, field: str) -> bool:
        return field in self._BYTE_FIELDS

    def __repr__(self) -> str:
        fields = "\n".join(
            f"  {name} = 0x{getattr(self, name):08X}"
            for name in self._OFFSETS
        )
        return f"GadgetAddresses(base=0x{self.base:08X})\n{fields}"


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


def build_weapons(array_base: int) -> tuple[dict[str, WeaponAddresses], dict[str, GadgetAddresses]]:
    weapons: dict[str, WeaponAddresses] = {}
    for i, name in enumerate(WEAPON_ORDER):
        if name is not None:
            weapons[name] = WeaponAddresses(array_base + i * WEAPON_STRUCT_SIZE)

    gadget_base = array_base + len(WEAPON_ORDER) * WEAPON_STRUCT_SIZE
    gadgets: dict[str, GadgetAddresses] = {}
    for i, name in enumerate(GADGET_ORDER):
        if name is not None:
            gadgets[name] = GadgetAddresses(gadget_base + i * WEAPON_STRUCT_SIZE)

    return weapons, gadgets


# Weapon state (runtime)

_MOD_SLOTS = ("mod_slot_one", "mod_slot_two", "mod_slot_three")

# Location-derived lookups depend on ``items`` and ``locations`` and are built
# lazily on first use to avoid the import cycle described at the top of the file.
_LOC_DATA_LOADED = False
VENDOR_WEAPON_LOC: dict[str, str] = {}
VENDOR_GADGET_LOC: dict[str, str] = {}
WEAPON_INTERNAL_TO_LOCATION: dict[str, str] = {}
GADGET_INTERNAL_TO_LOCATION: dict[str, str] = {}
_MOD_LOC: dict[str, tuple[str, str]] = {}
MOD_INTERNAL_TO_LOCATION: dict[tuple[str, str], str] = {}

_SLOT_TO_UNLOCK_ATTR: dict[str, str] = {
    "mod_slot_one": "mod_unlock_one",
    "mod_slot_two": "mod_unlock_two",
    "mod_slot_three": "mod_unlock_three",
}

# (internal_weapon, mod_unlock_attr) -> planet the vendor selling that mod
# lives on. Drives the mod_unlock_N "purchasable" byte: it should only read 1
# once the player owns the weapon (and, on Challax, the extra gadgets below —
# that vendor sits behind the Polarizer gate, mirroring rules/challax.py's _base).
MOD_UNLOCK_PLANET: dict[tuple[str, str], str] = {}

# Planets whose mod vendor requires extra gadgets beyond owning the weapon
# itself, mirroring that planet's AP access_rule for its mod locations.
MOD_UNLOCK_EXTRA_GADGETS: dict[str, tuple[str, ...]] = {}


def _ensure_loc_data() -> None:
    """Populate the location/item-derived module globals (lazy, idempotent)."""
    global _LOC_DATA_LOADED, VENDOR_WEAPON_LOC, VENDOR_GADGET_LOC
    global WEAPON_INTERNAL_TO_LOCATION, GADGET_INTERNAL_TO_LOCATION
    global _MOD_LOC, MOD_INTERNAL_TO_LOCATION
    global MOD_UNLOCK_PLANET, MOD_UNLOCK_EXTRA_GADGETS
    if _LOC_DATA_LOADED:
        return
    from ..constants import Rac5GadgetKeys, Rac5Planets
    from ..locations import (
        GADGET_INTERNAL_TO_LOCATION as _GADGET_INTERNAL_TO_LOCATION,
        MOD_INTERNAL_TO_LOCATION as _MOD_INTERNAL_TO_LOCATION,
        VENDOR_GADGET_LOC as _VENDOR_GADGET_LOC,
        VENDOR_WEAPON_LOC as _VENDOR_WEAPON_LOC,
        WEAPON_INTERNAL_TO_LOCATION as _WEAPON_INTERNAL_TO_LOCATION,
        WEAPON_MOD_VENDOR_LOCATIONS as _WEAPON_MOD_VENDOR_LOCATIONS,
    )
    VENDOR_WEAPON_LOC = _VENDOR_WEAPON_LOC
    VENDOR_GADGET_LOC = _VENDOR_GADGET_LOC
    WEAPON_INTERNAL_TO_LOCATION = _WEAPON_INTERNAL_TO_LOCATION
    GADGET_INTERNAL_TO_LOCATION = _GADGET_INTERNAL_TO_LOCATION
    MOD_INTERNAL_TO_LOCATION = _MOD_INTERNAL_TO_LOCATION
    _MOD_LOC = {v: k for k, v in _MOD_INTERNAL_TO_LOCATION.items()}
    MOD_UNLOCK_PLANET = {
        (weapon, _SLOT_TO_UNLOCK_ATTR[slot]): _WEAPON_MOD_VENDOR_LOCATIONS[loc].region
        for (weapon, slot), loc in _MOD_INTERNAL_TO_LOCATION.items()
    }
    MOD_UNLOCK_EXTRA_GADGETS = {
        Rac5Planets.CHALLAX: (Rac5GadgetKeys.SHRINK_RAY, Rac5GadgetKeys.POLARIZER),
    }
    _LOC_DATA_LOADED = True


def __getattr__(name: str):
    # Resolve the lazily-built location lookups when imported via
    # ``from core.weapons import <name>`` (e.g. by core._hooks / core.vendor).
    if name in (
        "VENDOR_WEAPON_LOC", "VENDOR_GADGET_LOC",
        "WEAPON_INTERNAL_TO_LOCATION", "GADGET_INTERNAL_TO_LOCATION",
        "MOD_INTERNAL_TO_LOCATION", "_MOD_LOC",
        "MOD_UNLOCK_PLANET", "MOD_UNLOCK_EXTRA_GADGETS",
    ):
        _ensure_loc_data()
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class WeaponState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
        log: Callable[..., None] | None = None,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        _ensure_loc_data()
        self._log = log or (lambda *a, **k: None)
        self.weapons: dict[str, bool]           = {}
        self.gadgets: dict[str, bool]           = {}
        self.mods: dict[str, dict[str, bool]]   = {}
        self.vendor_locations: dict[str, bool]  = dict.fromkeys(
            (*VENDOR_WEAPON_LOC, *VENDOR_GADGET_LOC, *_MOD_LOC), False
        )
        # _make_weapon_handler/_make_gadget_handler return a fresh closure on
        # every call, so register/unregister must reuse the exact same
        # function objects — otherwise remove_struct_handler's identity check
        # silently no-ops and handlers pile up at the same address on every
        # planet revisit.
        self._registered_handlers: dict[type, Callable[[int, bytes], None]] = {}

    def on_exit(self) -> None:
        self.weapons.clear()
        self.gadgets.clear()
        self.mods.clear()

    def _register_handlers(self) -> None:
        for cls in self.addresses.structs():
            if issubclass(cls, WeaponStruct) and cls is not WeaponStruct:
                handler = self._registered_handlers.setdefault(cls, self._make_weapon_handler(cls.__name__))
                self.accessor.on_struct_change(cls, handler)
            elif issubclass(cls, GadgetStruct) and cls is not GadgetStruct:
                handler = self._registered_handlers.setdefault(cls, self._make_gadget_handler(cls.__name__))
                self.accessor.on_struct_change(cls, handler)

    def _unregister_handlers(self) -> None:
        for cls in self.addresses.structs():
            handler = self._registered_handlers.pop(cls, None)
            if handler is not None:
                self.accessor.remove_struct_handler(cls, handler)

    def _make_weapon_handler(self, cls_name: str):
        weapon_name = cls_name.removeprefix("WeaponStruct_")

        def handler(address: int, new_bytes: bytes) -> None:
            self._log(
                f"[RAC] WeaponState: struct change {weapon_name} @ {address:#010x} "
                f"raw={new_bytes.hex()}"
            )
            instance     = WeaponStruct.from_bytes(new_bytes)
            was_unlocked = self.weapons.get(weapon_name, False)
            is_unlocked  = bool(instance.unlocked)
            # Never regress True->False here: weapons aren't lost in this game,
            # and apply_vendor_locations()/set_unlocked() deliberately zero this
            # bit for vendor-display purposes (showing "buy weapon" instead of
            # "buy ammo") without the player actually losing AP ownership. If
            # this dict followed the bit down to False, owned_names() would
            # wrongly think an owned-but-not-yet-vendor-purchased weapon (e.g.
            # Scorcher) isn't owned at all the moment the default view locks it.
            if is_unlocked:
                self.weapons[weapon_name] = True
            prev_mods = dict(self.mods.get(weapon_name, dict.fromkeys(_MOD_SLOTS, False)))
            self.mods.setdefault(weapon_name, dict.fromkeys(_MOD_SLOTS, False))
            self.mods[weapon_name]["mod_slot_one"]   = bool(instance.mod_slot_one)
            self.mods[weapon_name]["mod_slot_two"]   = bool(instance.mod_slot_two)
            self.mods[weapon_name]["mod_slot_three"] = bool(instance.mod_slot_three)
            if is_unlocked and not was_unlocked:
                self._log(f"[RAC] WeaponState: {weapon_name} unlocked -> on_weapon_acquired")
                self.on_weapon_acquired(weapon_name)
            elif not is_unlocked and was_unlocked:
                self._log(f"[RAC] WeaponState: {weapon_name} lost -> on_weapon_lost")
                self.on_weapon_lost(weapon_name)
            for slot in _MOD_SLOTS:
                is_mod  = self.mods[weapon_name][slot]
                was_mod = prev_mods.get(slot, False)
                if is_mod and not was_mod:
                    self._log(f"[RAC] WeaponState: {weapon_name}.{slot} 0->1 -> on_mod_acquired")
                    self.on_mod_acquired(weapon_name, slot)
                elif not is_mod and was_mod:
                    self._log(f"[RAC] WeaponState: {weapon_name}.{slot} 1->0 -> on_mod_lost")
                    self.on_mod_lost(weapon_name, slot)
        return handler

    def _make_gadget_handler(self, cls_name: str):
        gadget_name = cls_name.removeprefix("GadgetStruct_")

        def handler(address: int, new_bytes: bytes) -> None:
            del address
            instance     = GadgetStruct.from_bytes(new_bytes)
            was_unlocked = self.gadgets.get(gadget_name, False)
            is_unlocked  = bool(instance.unlocked)
            # See _make_weapon_handler — same monotonic guard against
            # vendor-display zero-writes wrongly erasing AP ownership.
            if is_unlocked:
                self.gadgets[gadget_name] = True
            if is_unlocked and not was_unlocked:
                self.on_gadget_acquired(gadget_name)
            elif not is_unlocked and was_unlocked:
                self.on_gadget_lost(gadget_name)
        return handler

    def sync(self) -> None:
        self._write_inventory()

    def sync_slots(self) -> None:
        for cls in self.addresses.structs():
            if issubclass(cls, WeaponStruct) and cls is not WeaponStruct:
                name = cls.__name__.removeprefix("WeaponStruct_")
                raw  = self.accessor.read_raw(cls.BASE_ADDRESS, cls.size())
                inst = WeaponStruct.from_bytes(raw)
                self.weapons[name] = bool(inst.unlocked)
                self.mods.setdefault(name, dict.fromkeys(_MOD_SLOTS, False))
                self.mods[name]["mod_slot_one"]   = bool(inst.mod_slot_one)
                self.mods[name]["mod_slot_two"]   = bool(inst.mod_slot_two)
                self.mods[name]["mod_slot_three"] = bool(inst.mod_slot_three)
            elif issubclass(cls, GadgetStruct) and cls is not GadgetStruct:
                name = cls.__name__.removeprefix("GadgetStruct_")
                raw  = self.accessor.read_raw(cls.BASE_ADDRESS, cls.size())
                inst = GadgetStruct.from_bytes(raw)
                self.gadgets[name] = bool(inst.unlocked)

    def _write_inventory(self) -> None:
        for cls in self.addresses.structs():
            if issubclass(cls, WeaponStruct) and cls is not WeaponStruct:
                name = cls.__name__.removeprefix("WeaponStruct_")
                inst = cls()
                inst.unlocked       = int(self.weapons.get(name, False))
                inst.mod_slot_one   = int(self.mods.get(name, {}).get("mod_slot_one", False))
                inst.mod_slot_two   = int(self.mods.get(name, {}).get("mod_slot_two", False))
                inst.mod_slot_three = int(self.mods.get(name, {}).get("mod_slot_three", False))
                self.accessor.write_raw(cls.BASE_ADDRESS, bytes(inst))
            elif issubclass(cls, GadgetStruct) and cls is not GadgetStruct:
                name = cls.__name__.removeprefix("GadgetStruct_")
                inst = cls()
                inst.unlocked = int(self.gadgets.get(name, False))
                self.accessor.write_field(cls, "unlocked", inst.unlocked)

    def apply_vendor_locations(self, allowed_extra: frozenset[str] = frozenset()) -> None:
        """Zero all weapon/gadget/mod memory then restore what the player may keep.

        Weapons/gadgets restored if purchased from vendor (and still owned) OR
        if name is in allowed_extra (owned weapon whose vendor planet is
        unlocked). Mods restored only if purchased from this vendor — owning
        the mod via an AP item received elsewhere does not restore it here.
        """
        weapon_classes = {
            cls.__name__.removeprefix("WeaponStruct_"): cls
            for cls in self.addresses.structs()
            if issubclass(cls, WeaponStruct) and cls is not WeaponStruct
        }
        gadget_classes = {
            cls.__name__.removeprefix("GadgetStruct_"): cls
            for cls in self.addresses.structs()
            if issubclass(cls, GadgetStruct) and cls is not GadgetStruct
        }

        # Compute the final desired state first, then write each field exactly
        # once — no separate zero pass followed by a restore pass.
        weapon_unlocked = dict.fromkeys(weapon_classes, False)
        weapon_mods: dict[str, dict[str, bool]] = {
            name: dict.fromkeys(_MOD_SLOTS, False) for name in weapon_classes
        }
        gadget_unlocked = dict.fromkeys(gadget_classes, False)

        for loc_name, purchased in self.vendor_locations.items():
            if not purchased:
                continue
            if loc_name in VENDOR_WEAPON_LOC:
                name = VENDOR_WEAPON_LOC[loc_name]
                # Guard: only restore if player actually owns it (edge-case safety).
                if self.weapons.get(name, False) and name in weapon_unlocked:
                    weapon_unlocked[name] = True
            elif loc_name in VENDOR_GADGET_LOC:
                name = VENDOR_GADGET_LOC[loc_name]
                if self.gadgets.get(name, False) and name in gadget_unlocked:
                    gadget_unlocked[name] = True
            elif loc_name in _MOD_LOC:
                weapon, slot = _MOD_LOC[loc_name]
                if weapon in weapon_mods:
                    weapon_mods[weapon][slot] = True

        # Weapons/gadgets owned via AP items whose vendor planet is unlocked.
        for name in allowed_extra:
            if name in weapon_unlocked:
                weapon_unlocked[name] = True
            if name in gadget_unlocked:
                gadget_unlocked[name] = True

        missing_allowed = [n for n in allowed_extra if n not in weapon_unlocked and n not in gadget_unlocked]
        self._log(
            f"[RAC] WeaponState.apply_vendor_locations: writing "
            f"{len(weapon_classes)} weapon struct(s) {sorted(weapon_classes)}, "
            f"{len(gadget_classes)} gadget struct(s) -> unlocked={[n for n, v in weapon_unlocked.items() if v]}"
            + (f" — NOT REGISTERED (no struct for): {missing_allowed}" if missing_allowed else "")
        )
        for name, cls in weapon_classes.items():
            self.accessor.write_field(cls, "unlocked", int(weapon_unlocked[name]))
            for slot in _MOD_SLOTS:
                self.accessor.write_field(cls, slot, int(weapon_mods[name][slot]))
        for name, cls in gadget_classes.items():
            self.accessor.write_field(cls, "unlocked", int(gadget_unlocked[name]))

    def zero_unpurchased_mod_slots(self, names: frozenset[str]) -> None:
        """Explicitly re-zero mod_slot_N for the given weapons unless that
        specific slot was actually bought from this vendor. apply_vendor_locations
        already does this as part of its zero/restore pass, but a Progressive-
        item grant (mod_slot_N=1, owned outright, unrelated to this vendor) can
        still race back in afterwards — calling this right after as a dedicated
        second pass guarantees the mod vendor shows it as purchasable rather
        than already-owned."""
        purchased_slots = {
            _MOD_LOC[loc] for loc, bought in self.vendor_locations.items()
            if bought and loc in _MOD_LOC
        }
        zeroed: list[str] = []
        for cls in self.addresses.structs():
            if not (issubclass(cls, WeaponStruct) and cls is not WeaponStruct):
                continue
            name = cls.__name__.removeprefix("WeaponStruct_")
            if name not in names:
                continue
            for slot in _MOD_SLOTS:
                if (name, slot) in purchased_slots:
                    continue
                # Read first — this runs every poll tick while the mod vendor
                # is open, so skip the write (and the log below) unless
                # something actually set it back to 1 since our last pass.
                if self.accessor.read_field(cls, slot):
                    self.accessor.write_field(cls, slot, 0)
                    zeroed.append(f"{name}.{slot}")
        if zeroed:
            self._log(
                f"[RAC] WeaponState.zero_unpurchased_mod_slots: re-zeroed {zeroed} "
                f"(was set to 1 despite not being in purchased_slots={sorted(purchased_slots)})"
            )

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        for loc in checked_locations:
            if loc in self.vendor_locations:
                self.vendor_locations[loc] = True
            if loc in VENDOR_WEAPON_LOC:
                self.weapons[VENDOR_WEAPON_LOC[loc]] = True
            elif loc in VENDOR_GADGET_LOC:
                self.gadgets[VENDOR_GADGET_LOC[loc]] = True
            elif loc in _MOD_LOC:
                weapon, slot = _MOD_LOC[loc]
                self.mods.setdefault(weapon, dict.fromkeys(_MOD_SLOTS, False))
                self.mods[weapon][slot] = True

    def has_weapon(self, name: str) -> bool:
        return self.weapons.get(name, False)

    def has_gadget(self, name: str) -> bool:
        return self.gadgets.get(name, False)

    def has_mod(self, weapon: str, slot: str) -> bool:
        return self.mods.get(weapon, {}).get(slot, False)

    def on_weapon_acquired(self, _name: str) -> None:
        del _name

    def on_weapon_lost(self, _name: str) -> None:
        del _name

    def on_gadget_acquired(self, _name: str) -> None:
        del _name

    def on_gadget_lost(self, _name: str) -> None:
        del _name

    def on_mod_acquired(self, _weapon: str, _slot: str) -> None:
        del _weapon, _slot

    def on_mod_lost(self, _weapon: str, _slot: str) -> None:
        del _weapon, _slot

    def __repr__(self) -> str:
        unlocked_w = [n for n, v in self.weapons.items() if v]
        unlocked_g = [n for n, v in self.gadgets.items() if v]
        return f"WeaponState(weapons={unlocked_w}, gadgets={unlocked_g})"

from __future__ import annotations

import struct as _struct
from collections.abc import Callable
from typing import TYPE_CHECKING, NamedTuple

from BaseClasses import ItemClassification

from ..constants import Rac5GadgetKeys, Rac5WeaponKeys
from .locations import weapon_locations as _weapon_locations

if TYPE_CHECKING:
    from ..pypine import Pine

# Vendor/mod location lookups live in core.locations.weapon_locations, not
# here — that module builds them lazily to avoid a circular import back into
# this module (items.py imports this module's weapon constants directly).


WEAPON_STRUCT_SIZE = 0x58
WEAPON_MIN_CONSECUTIVE = 4

# ProgressiveWeapons option values (options.py's ProgressiveWeapons Choice)
# — kept in sync manually.
PROGRESSIVE_OFF       = 0
PROGRESSIVE_MANUAL    = 1
PROGRESSIVE_AUTOMATIC = 2

class WeaponData(NamedTuple):
    is_projectile: bool
    classification: ItemClassification
    max_level: int
    mod_count: int
    # 1-indexed experience thresholds (exp_thresholds[0] = XP for level 2).
    # Levels 5-8 have no threshold yet, so PROGRESSIVE_MANUAL imposes no ceiling past level 4.
    exp_thresholds: tuple[int, ...] = ()


# Single source of truth per weapon (keyed by internal Rac5WeaponKeys).
# WEAPON_MAX_LEVELS/WEAPON_MOD_COUNTS/WEAPON_EXP_THRESHOLDS below are derived
# from this.
WEAPON_DATA: dict[str, WeaponData] = {
    Rac5WeaponKeys.LACERATOR: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=8, mod_count=2,
        exp_thresholds=(3000, 9000, 15000, None, 27000, 55000, 205000, None),
    ),
    Rac5WeaponKeys.CONCUSSION_GUN: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=8, mod_count=3,
        exp_thresholds=(6000, 9000, 12000, None, 50000, 78000, 158000, None),
    ),
    Rac5WeaponKeys.ACID_BOMB_GLOVE: WeaponData(
        is_projectile=False, classification=ItemClassification.progression, max_level=8, mod_count=2,
        exp_thresholds=(3000, 6000, 9000, None, 27_000, 55_000, 55_000, None),
    ),
    Rac5WeaponKeys.AGENTS_OF_DOOM: WeaponData(
        is_projectile=False, classification=ItemClassification.progression, max_level=8, mod_count=2,
        exp_thresholds=(6000, 9000, 12000, None, 27_000, 100_000, 250_000, None),
    ),
    Rac5WeaponKeys.BEE_MINE_GLOVE: WeaponData(
        is_projectile=False, classification=ItemClassification.progression, max_level=8, mod_count=2,
        exp_thresholds=(6000, 7500, 9000, None, 50_000, 142_000, 225_000, None),
    ),
    Rac5WeaponKeys.STATIC_BARRIER: WeaponData(
        is_projectile=False, classification=ItemClassification.useful, max_level=8, mod_count=2,
        exp_thresholds=(15000, 18000, 21000, None, 24_000, 27_000, 30_000, None),
    ),
    Rac5WeaponKeys.SHOCK_ROCKET: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=8, mod_count=3,
        exp_thresholds=(15000, 19000, 42000, None, 60_000, 145_000, 250_000, None),
    ),
    Rac5WeaponKeys.SNIPER_MINE: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=8, mod_count=2,
        exp_thresholds=(4000, 5500, 7000, None, 50_000, 142_000, 225_000, None),
    ),
    Rac5WeaponKeys.SCORCHER: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=8, mod_count=2,
        exp_thresholds=(7000, 8500, 10000, None, 27_000, 55_000, 205_000, None),
    ),
    Rac5WeaponKeys.LASER_TRACER: WeaponData(
        is_projectile=True, classification=ItemClassification.progression, max_level=8, mod_count=2,
        exp_thresholds=(15000, 27000, 45000, None, 65_000, 225_000, 350_000, None),
    ),
    Rac5WeaponKeys.SUCK_CANNON: WeaponData(
        is_projectile=True, classification=ItemClassification.useful, max_level=8, mod_count=1,
        exp_thresholds=(3500, 5000, 7000, None, 12_500, 43_000, 67_500, None),
    ),
    Rac5WeaponKeys.MOOTATOR: WeaponData(
        is_projectile=False, classification=ItemClassification.progression, max_level=8, mod_count=0,
        exp_thresholds=(12000, 12000, 16000, None, 50_000, 142_000, 225_000, None),
    ),
    Rac5WeaponKeys.RYNO: WeaponData(
        # RYNO has no Titan variant — stays capped at 4.
        is_projectile=True, classification=ItemClassification.progression, max_level=4, mod_count=0,
        exp_thresholds=(85000, 350000, 999000, None),
    ),
}

# Every weapon with a Challenge Mode Titan variant (all except RYNO).
TITAN_ELIGIBLE_WEAPONS: frozenset[str] = frozenset(
    key for key in WEAPON_DATA if key != Rac5WeaponKeys.RYNO
)


class VendorDisplayAmmo(NamedTuple):
    """Ammo count shown while the weapons vendor's buy-new view displays this weapon;
    `titan` is shown once Titan-pending, None for RYNO (no Titan variant)."""
    base: int
    titan: int | None = None


WEAPON_VENDOR_DISPLAY_AMMO: dict[str, VendorDisplayAmmo] = {
    Rac5WeaponKeys.LACERATOR:       VendorDisplayAmmo(base=60, titan=120),
    Rac5WeaponKeys.CONCUSSION_GUN:  VendorDisplayAmmo(base=25, titan=30),
    Rac5WeaponKeys.ACID_BOMB_GLOVE: VendorDisplayAmmo(base=5, titan=10),
    Rac5WeaponKeys.AGENTS_OF_DOOM:  VendorDisplayAmmo(base=6, titan=10),
    Rac5WeaponKeys.BEE_MINE_GLOVE:  VendorDisplayAmmo(base=8, titan=8),
    Rac5WeaponKeys.STATIC_BARRIER:  VendorDisplayAmmo(base=5, titan=5),
    Rac5WeaponKeys.SHOCK_ROCKET:    VendorDisplayAmmo(base=20, titan=22),
    Rac5WeaponKeys.SNIPER_MINE:     VendorDisplayAmmo(base=8, titan=10),
    Rac5WeaponKeys.SCORCHER:        VendorDisplayAmmo(base=60, titan=90),
    Rac5WeaponKeys.LASER_TRACER:    VendorDisplayAmmo(base=200, titan=300),
    Rac5WeaponKeys.SUCK_CANNON:     VendorDisplayAmmo(base=8, titan=16),
    Rac5WeaponKeys.MOOTATOR:        VendorDisplayAmmo(base=0, titan=0),
    Rac5WeaponKeys.RYNO:            VendorDisplayAmmo(base=30),
}

WEAPON_MOD_COUNTS: dict[str, int] = {key: data.mod_count for key, data in WEAPON_DATA.items()}

WEAPON_MAX_LEVELS: dict[str, int] = {key: data.max_level for key, data in WEAPON_DATA.items()}

# Per-weapon tuple of fixed experience thresholds, 1-indexed by level reached
# (see WeaponData.exp_thresholds).
WEAPON_EXP_THRESHOLDS: dict[str, tuple[int, ...]] = {
    key: data.exp_thresholds for key, data in WEAPON_DATA.items()
}


def exp_threshold_for_level(weapon: str, level: int) -> int | None:
    """Fixed experience value required to reach `level` (1-indexed) for `weapon`,
    or None if there's no threshold for that level."""
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


class WeaponInt32Field:
    """Pine-backed accessor for a single int32 weapon struct field."""

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
    """Pine-backed live accessor for one weapon struct instance — every
    field reads/writes memory directly via its descriptor."""

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
        # First live accessor for this offset (already sanity-checked in
        # is_weapon_candidate); used by AmmoLink to mirror ammo across players.
        "ammo":             0x31,
    }

    level            = WeaponInt32Field("level")
    experience       = WeaponInt32Field("experience")
    ammo             = WeaponInt32Field("ammo")
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


def build_weapons(array_base: int | None, pine: Pine) -> tuple[dict[str, WeaponAddresses], dict[str, GadgetAddresses]]:
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
    """Pine-backed live accessor + ownership/vendor tracking for weapons, gadgets and
    mods. Planet-dependent: call set_base(array_base) whenever the loaded planet changes."""

    def __init__(self, pine: Pine) -> None:
        self.pine = pine
        _weapon_locations._ensure_loc_data()
        self.weapons: dict[str, bool]         = {}
        self.gadgets: dict[str, bool]         = {}
        self.mods: dict[str, dict[str, bool]] = {}
        # Raw-memory baselines for check()'s 0->1 flip detection, kept separate from
        # weapons/gadgets/mods (which never regress True->False) so a display
        # zero/restore cycle doesn't hide a real repurchase.
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
        # Last-seen raw experience per weapon, used only to diff this tick's
        # gain from the last one — see apply_experience_boost().
        self._prev_experience: dict[str, int] = {}

        # ProgressiveWeapons option (options.py): 0=off, 1=manual, 2=automatic.
        # Set directly by the client from slot_data.
        self.progressive_mode: int = PROGRESSIVE_OFF
        # Per-weapon max allowed level (0-indexed); kept current by Core.apply_inventory().
        # Absent = zero copies received (fully locked).
        self.level_caps: dict[str, int] = {}
        # Manual mode, cap < 0: pins experience so a fully-locked weapon's XP
        # never moves; captured on first observation, cleared once a copy arrives.
        self._pinned_experience: dict[str, int] = {}

        # Gates the Titan purchase mechanism below; 0 = off.
        self.challenge_mode: int = 0
        # Floors level at 5 (0-indexed 4) once a Titan variant is bought, caps
        # at 4 while not; rebuilt from AP's checked_locations on reconnect.
        self.titan_purchased: dict[str, bool] = dict.fromkeys(TITAN_ELIGIBLE_WEAPONS, False)

    def set_base(self, array_base: int | None) -> None:
        """Rebind every weapon/gadget address to the planet's array base, or unbind
        entirely (check()/sync() become no-ops) when array_base is None."""
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

    def get_experience(self, weapon: str) -> int:
        addr = self._weapon_addrs.get(weapon)
        if addr is None:
            return 0
        return addr.experience

    def set_experience(self, weapon: str, value: int) -> None:
        addr = self._weapon_addrs.get(weapon)
        if addr is not None:
            addr.experience = value

    def get_ammo(self, weapon: str) -> int:
        addr = self._weapon_addrs.get(weapon)
        if addr is None:
            return 0
        return addr.ammo

    def set_ammo(self, weapon: str, value: int) -> None:
        """Write a weapon's ammo directly, for AmmoLink to mirror a shared value in;
        doesn't distinguish that from organic gain/spend, unlike set_level()/experience."""
        addr = self._weapon_addrs.get(weapon)
        if addr is not None:
            addr.ammo = value

    def get_level(self, weapon: str) -> int:
        addr = self._weapon_addrs.get(weapon)
        if addr is None:
            return 0
        return addr.level

    def set_level(self, weapon: str, level: int) -> None:
        """Write a weapon's level directly (a synthetic write, not an organic level-up).
        Also rebaselines _raw_level so check() doesn't fire spurious level checks."""
        addr = self._weapon_addrs.get(weapon)
        if addr is not None:
            addr.level = level
        self._raw_level[weapon] = level

    def zero_levels_for_vendor(self, purchasable: frozenset[str] | None = None) -> dict[str, int]:
        """Snapshot every weapon's level, then zero out the ones in `purchasable` so the
        vendor's level-derived price doesn't leak a leveled-but-unowned weapon's real
        price; caller must pass the snapshot to restore_levels() once the vendor closes."""
        snapshot = {name: addr.level for name, addr in self._weapon_addrs.items()}
        for name, addr in self._weapon_addrs.items():
            if purchasable is None or name in purchasable:
                addr.level = 0
                self._raw_level[name] = 0
        return snapshot

    def restore_levels(self, snapshot: dict[str, int]) -> None:
        """Write back a snapshot taken by zero_levels_for_vendor(), also rebaselining
        _raw_level so check() doesn't misread the restore as a fresh level-up."""
        for name, level in snapshot.items():
            addr = self._weapon_addrs.get(name)
            if addr is not None:
                addr.level = level
            self._raw_level[name] = level

    def snapshot_ammo(self, names: frozenset[str] | None = None) -> dict[str, int]:
        """Read live ammo for `names` (or every weapon) — the counterpart to
        restore_ammo(), for VendorInventory's display override."""
        if names is None:
            return {name: addr.ammo for name, addr in self._weapon_addrs.items()}
        return {
            name: addr.ammo for name, addr in self._weapon_addrs.items() if name in names
        }

    def restore_ammo(self, snapshot: dict[str, int]) -> None:
        """Write back a snapshot taken by snapshot_ammo()."""
        for name, ammo in snapshot.items():
            addr = self._weapon_addrs.get(name)
            if addr is not None:
                addr.ammo = ammo

    def get_mod_unlock(self, weapon: str, attr: str) -> bool:
        addr = self._weapon_addrs.get(weapon)
        if addr is None:
            return False
        return bool(getattr(addr, attr))

    def set_mod_unlock(self, weapon: str, attr: str, value: bool) -> None:
        """Write the mod_unlock_N "purchasable" byte — separate from set_mod (ownership),
        this just controls whether the mod vendor shows that slot as buyable."""
        addr = self._weapon_addrs.get(weapon)
        if addr is not None:
            setattr(addr, attr, value)

    def check(self) -> dict[str, list]:
        """Batch-read every weapon/gadget/mod byte, update ownership state, and return
        what newly changed since the raw memory's last reading (not weapons/gadgets/mods,
        which never regress, so a repurchase of an already-owned item wouldn't show)."""
        newly_weapons: list[str] = []
        newly_gadgets: list[str] = []
        newly_mods: list[tuple[str, str]] = []
        newly_levels: list[tuple[str, int]] = []
        newly_titans: list[str] = []

        weapon_names = list(self._weapon_addrs)
        gadget_names = list(self._gadget_addrs)

        byte_addrs: list[int] = []
        byte_spec: list[tuple[str, str]] = []
        for name in weapon_names:
            addr = self._weapon_addrs[name]
            for field in ("unlocked", *_MOD_SLOTS):
                byte_addrs.append(addr.base + addr._OFFSETS[field])
                byte_spec.append((name, field))
        for name in gadget_names:
            addr = self._gadget_addrs[name]
            byte_addrs.append(addr.base + addr._OFFSETS["unlocked"])
            byte_spec.append((name, "unlocked"))

        level_addrs = [
            self._weapon_addrs[name].base + self._weapon_addrs[name]._OFFSETS["level"]
            for name in weapon_names
        ]

        byte_values  = self.pine.batch_read_int8(byte_addrs) if byte_addrs else []
        level_values = self.pine.batch_read_int32(level_addrs) if level_addrs else []
        bytes_by_key: dict[tuple[str, str], int] = dict(zip(byte_spec, byte_values, strict=True))
        levels_by_name: dict[str, int] = dict(zip(weapon_names, level_values, strict=True))

        for name in weapon_names:
            was_unlocked = self._raw_weapons.get(name, False)
            is_unlocked  = bool(bytes_by_key[(name, "unlocked")])
            self._raw_weapons[name] = is_unlocked
            if is_unlocked:
                self.weapons[name] = True
            if is_unlocked and not was_unlocked:
                newly_weapons.append(name)

            prev_mods = dict(self._raw_mods.get(name, dict.fromkeys(_MOD_SLOTS, False)))
            raw_mods  = self._raw_mods.setdefault(name, dict.fromkeys(_MOD_SLOTS, False))
            mods      = self.mods.setdefault(name, dict.fromkeys(_MOD_SLOTS, False))
            for slot in _MOD_SLOTS:
                slot_unlocked = bool(bytes_by_key[(name, slot)])
                raw_mods[slot] = slot_unlocked
                if slot_unlocked:
                    mods[slot] = True
                if slot_unlocked and not prev_mods.get(slot, False):
                    newly_mods.append((name, slot))

            if is_unlocked:
                prev_level = self._raw_level.get(name, -1)
                current_level = levels_by_name[name]
                if current_level > prev_level:
                    # Level 1 is deliberately excluded — synonymous with owning the weapon.
                    for idx in range(prev_level + 1, current_level + 1):
                        level = idx + 1
                        if level >= 2:
                            newly_levels.append((name, level))
                        # Reaching level 5 is what buying a Titan variant looks like in-game.
                        if level == 5 and name in TITAN_ELIGIBLE_WEAPONS:
                            newly_titans.append(name)
                self._raw_level[name] = current_level

        for name in gadget_names:
            was_unlocked = self._raw_gadgets.get(name, False)
            is_unlocked  = bool(bytes_by_key[(name, "unlocked")])
            self._raw_gadgets[name] = is_unlocked
            if is_unlocked:
                self.gadgets[name] = True
            if is_unlocked and not was_unlocked:
                newly_gadgets.append(name)

        return {
            "weapons": newly_weapons, "gadgets": newly_gadgets,
            "mods": newly_mods, "levels": newly_levels, "titans": newly_titans,
        }

    def apply_experience_boost(self) -> None:
        """Inflate each weapon's experience gain by experience_multiplier every tick.
        Diffed against _prev_experience so only genuine in-game gain gets amplified,
        never our own previous write; stops once a weapon reaches its max level."""
        multiplier = self.experience_multiplier
        for name, addr in self._weapon_addrs.items():
            current  = addr.experience
            previous = self._prev_experience.get(name)
            if previous is None:
                self._prev_experience[name] = current
                continue
            diff = current - previous
            if diff <= 0:
                self._prev_experience[name] = current
                continue
            max_level_idx = WEAPON_MAX_LEVELS.get(name, 4) - 1
            if multiplier > 1 and addr.level < max_level_idx:
                boosted = previous + diff * multiplier
                addr.experience = boosted
                self._prev_experience[name] = boosted
            else:
                self._prev_experience[name] = current

    def _titan_bound(self, name: str) -> tuple[int | None, int | None]:
        """(ceiling, floor) Challenge Mode Titan bounds for `name`: (3, None) before its
        Titan variant is bought, (None, 4) after, (None, None) if not applicable."""
        if self.challenge_mode < 1 or name not in TITAN_ELIGIBLE_WEAPONS:
            return None, None
        if self.titan_purchased.get(name, False):
            return None, 4
        return 3, None

    def apply_progressive_leveling(self) -> None:
        """Gate weapon leveling behind Progressive Weapon items and/or Challenge Mode
        Titan purchase every tick. automatic pins level to cap and zeroes experience;
        manual clamps experience to the next threshold so a boosted tick's gain can't skip a level."""
        mode = self.progressive_mode
        titan_active = self.challenge_mode >= 1
        if mode == PROGRESSIVE_OFF and not titan_active:
            return

        for name, addr in self._weapon_addrs.items():
            titan_ceiling, titan_floor = self._titan_bound(name) if titan_active else (None, None)

            if mode == PROGRESSIVE_OFF:
                if titan_ceiling is not None and addr.level > titan_ceiling:
                    addr.level = titan_ceiling
                    addr.experience = 0
                elif titan_floor is not None and addr.level < titan_floor:
                    addr.level = titan_floor
                    addr.experience = 0
                continue

            cap = self.level_caps.get(name, -1)
            if titan_floor is not None:
                cap = max(cap, titan_floor)
            elif titan_ceiling is not None and cap > titan_ceiling:
                # Enough copies to earn past level 4, but only once level 4 is actually reached.
                if addr.level < titan_ceiling:
                    cap = titan_ceiling
            elif titan_ceiling is not None:
                cap = min(cap, titan_ceiling)

            if mode == PROGRESSIVE_AUTOMATIC:
                addr.level = max(cap, 0)
                addr.experience = 0
                continue

            # manual
            if cap < 0:
                # No Progressive copies received yet — fully locked.
                pinned = self._pinned_experience.get(name)
                if pinned is None:
                    self._pinned_experience[name] = addr.experience
                else:
                    addr.experience = pinned
                continue
            self._pinned_experience.pop(name, None)

            if addr.level > cap:
                # Shouldn't normally happen (caps only rise), but pull back
                # down defensively rather than leave it over-leveled.
                addr.level = cap

            max_level_idx = WEAPON_MAX_LEVELS.get(name, cap + 1) - 1
            if cap >= max_level_idx:
                # Every copy received — fully unlocked, no ceiling at all.
                continue

            if addr.level == cap:
                # Already at the max permitted level; keep experience at 0
                # rather than let it climb with no level to show for it.
                if addr.experience != 0:
                    addr.experience = 0
                continue

            # Check the threshold for the level after the CURRENT one, not
            # cap's own level, since cap can sit several levels ahead.
            next_threshold = exp_threshold_for_level(name, addr.level + 2)
            if next_threshold is None:
                # No fixed threshold for this gap (e.g. level 5, the Titan tier),
                # so bump the level across manually since the game can't do it on its own.
                addr.level += 1
                addr.experience = 0
            else:
                # Never let a single boosted tick's gain carry past the ceiling in one jump.
                ceiling = exp_threshold_for_level(name, cap + 1)
                if ceiling is not None and addr.experience > ceiling:
                    addr.experience = ceiling

    def wipe(self) -> None:
        """Zero every weapon/gadget/mod unlock bit, level and experience, and rebaseline
        every tracking dict. Called once on first planet-ready after connect, or
        stale save progress would look like a batch of brand-new pickups."""
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
        # Deliberately NOT resetting titan_purchased — wipe() can run after
        # sync_from_ap() has already restored it, and resetting would re-open
        # every already-bought Titan variant for purchase.

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
        """Read the current planet's array into the ownership dicts (no change report).
        Also re-baselines check()'s raw-memory dicts so it doesn't see this resync as a change."""
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
            # Rebaseline so apply_experience_boost() doesn't mistake a fresh
            # planet's array value for a same-tick gain.
            self._prev_experience[name] = addr.experience
            # _raw_level deliberately NOT rebaselined, so a precollected weapon
            # still fires every level up to its current one on first observation.
        for name, addr in self._gadget_addrs.items():
            unlocked = bool(addr.unlocked)
            self.gadgets[name]      = unlocked
            self._raw_gadgets[name] = unlocked

    def apply_vendor_locations(self, allowed_extra: frozenset[str] = frozenset()) -> None:
        """Zero all weapon/gadget/mod memory then restore what the player may keep:
        purchased-and-owned or in allowed_extra for weapons/gadgets; purchased-only for mods."""
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
        """Re-zero mod_slot_N unless bought from this vendor, since a Progressive-item
        grant can race back in after apply_vendor_locations()'s own zero/restore pass."""
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
                # Read first to skip the write unless it flipped back since our last pass.
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
            elif loc in _weapon_locations._TITAN_LOC:
                self.titan_purchased[_weapon_locations._TITAN_LOC[loc]] = True

    def level_experience_snapshot(self) -> dict[str, list[int]]:
        """Current [level, experience] per weapon, for persisting to AP data storage so
        real leveling progress survives wipe() on reconnect. Lists, not tuples — JSON has no tuple type."""
        return {name: [addr.level, addr.experience] for name, addr in self._weapon_addrs.items()}

    def restore_level_experience(self, data: dict) -> None:
        """Write back a level_experience_snapshot(), also rebaselining _raw_level/
        _prev_experience so check() doesn't misread the restore as a fresh gain."""
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
        """Zero unlocked + every mod slot for every weapon is_ap_owned says no to.
        Cleans up the mod vendor's temporary display hack, since apply_inventory()'s
        resync is additive-only and wouldn't undo it on its own."""
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

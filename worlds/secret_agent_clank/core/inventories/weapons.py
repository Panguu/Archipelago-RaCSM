"""Shared native GadgetData array for Ratchet and Clank weapons, tools and abilities."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ...constants.weapon_order import WEAPON_ORDER, WeaponSlot

if TYPE_CHECKING:
    from ...pypine import Pine

# --- Struct layout (see docs/ for the full field write-up; only the two
# fields this module actually tracks are given names here) -----------------
WEAPON_STRUCT_SIZE: int = 0x74  # 116 bytes per entry, 40 entries per array

_OFFSET_NAME_PTR     = 0x00  # char* -- not read live here, only used to derive WEAPON_ORDER once
_OFFSET_CATEGORY     = 0x04  # int -- 2=Ratchet weapon, 1=Ratchet tool/item, 3=wrench ability (not read live here)
_OFFSET_CURRENT_AMMO = 0x60  # int32 -- current ammo/charge count
_OFFSET_OWNED_FLAG   = 0x70  # int32 -- 0 = not picked up yet, nonzero = owned

# --- Mod-install flags (CONFIRMED via a clean live before/after byte diff of
# the entire 40-slot table across a real in-game vendor mod purchase -- see
# docs/) -----------------------------------------------------------------
# One byte per mod slot, 3 slots per weapon. A weapon-mod purchase in
# SCRNMODVENDOR (see FUN_003d42b0 -> FUN_0035c3d8 in the Ghidra decompile)
# writes 1 to *(byte*)(GadgetData_base + slot + 0x68) once the mod is
# installed -- this table IS that GadgetData layout, not a separate struct.
# Live evidence: bought one weapon mod, bolts dropped by exactly 15000 (a
# different, smaller price than the flat 35000 charged for a bare weapon
# unlock), and diffing a before/after snapshot of the ENTIRE 4640-byte
# table found exactly one changed byte in the whole array: slot 9
# ("minelauncher"), struct offset 0x69, 0x00 -> 0x01 -- i.e. mod slot 1
# (0x68 + 1) for that weapon. Every other byte in every other slot was
# byte-for-byte identical before and after.
_OFFSET_MOD_SLOTS = 0x68  # 3 consecutive bytes: mod slot 0/1/2 installed-flags
MOD_SLOT_COUNT    = 3

class WeaponInt32Field:
    """Descriptor for a 4-byte int field at a fixed offset within a WeaponAddresses instance's struct entry."""
    __slots__ = ("offset",)

    def __init__(self, offset: int) -> None:
        self.offset = offset

    def __get__(self, instance: WeaponAddresses | None, owner: object = None) -> int:
        if instance is None:
            return self  # type: ignore[return-value]
        return instance.pine.read_int32(instance.base + self.offset)

    def __set__(self, instance: WeaponAddresses, value: int) -> None:
        instance.pine.write_int32(instance.base + self.offset, value)


class WeaponAddresses:
    """One weapon's live struct entry."""

    ammo  = WeaponInt32Field(_OFFSET_CURRENT_AMMO)
    owned = WeaponInt32Field(_OFFSET_OWNED_FLAG)

    def __init__(self, base: int, pine: Pine) -> None:
        self.base = base
        self.pine = pine

    def mod_installed(self, slot: int) -> bool:
        """True if mod slot `slot` (0/1/2) is installed on this weapon -- see _OFFSET_MOD_SLOTS above."""
        if not (0 <= slot < MOD_SLOT_COUNT):
            raise ValueError(f"mod slot must be 0-{MOD_SLOT_COUNT - 1}, got {slot}")
        return bool(self.pine.read_int8(self.base + _OFFSET_MOD_SLOTS + slot))

    def grant_mod(self, slot: int) -> None:
        """Directly write the installed flag for mod slot `slot` (0/1/2) -- the same write SCRNMODVENDOR's purchase flow performs after deducting bolts (see _OFFSET_MOD_SLOTS docstring), minus the purchase."""
        if not (0 <= slot < MOD_SLOT_COUNT):
            raise ValueError(f"mod slot must be 0-{MOD_SLOT_COUNT - 1}, got {slot}")
        self.pine.write_int8(self.base + _OFFSET_MOD_SLOTS + slot, 1)

    def __repr__(self) -> str:
        return f"WeaponAddresses(base=0x{self.base:X})"


def build_weapons(array_base: int | None, pine: Pine) -> dict[str, WeaponAddresses]:
    """Bind every named slot in WEAPON_ORDER to its live struct entry."""
    if array_base is None:
        return {}
    weapons: dict[str, WeaponAddresses] = {}
    for i, name in enumerate(WEAPON_ORDER):
        if name is not None:
            weapons[name] = WeaponAddresses(array_base + i * WEAPON_STRUCT_SIZE, pine)
    return weapons


class WeaponInventory:
    """Drop-in replacement for core/inventory.py's ItemInventory, scoped to Ratchet's WeaponData-table weapons -- same check()/apply_all()/ strip_all() method names and signatures as ItemInventory, so core/core.py and core/planets.py don't need any call-site changes beyond constructing this instead and calling set_base() instead of set_addrs()."""

    def __init__(self, pine: Pine) -> None:
        self.pine = pine
        self.weapons: dict[str, WeaponAddresses] = {}
        # Last-known owned state (0/1), used by check() to detect 0->1
        # flips without re-reading every weapon serially.
        self._raw_owned: dict[str, int] = {}
        # Last-known mod-slot state ([0/1, 0/1, 0/1] per weapon), used by
        # check_mods() the same way _raw_owned is used by check().
        self._raw_mods: dict[str, list[int]] = {}

    def set_base(self, array_base: int | None) -> None:
        """Rebind every weapon to the newly-loaded case's array base, or unbind entirely when array_base is None (unrecognized/no case)."""
        self.weapons = build_weapons(array_base, self.pine)
        self._raw_owned = dict.fromkeys(self.weapons, 0)
        self._raw_mods = {name: [0] * MOD_SLOT_COUNT for name in self.weapons}

    # -- Single-weapon convenience accessors (not batched -- fine for
    # one-off reads/writes, e.g. from a debug command) ----------------------

    def has_weapon(self, name: str) -> bool:
        w = self.weapons.get(name)
        return bool(w.owned) if w is not None else False

    def get_ammo(self, name: str) -> int:
        w = self.weapons.get(name)
        return w.ammo if w is not None else 0

    def set_ammo(self, name: str, value: int) -> None:
        w = self.weapons.get(name)
        if w is not None:
            w.ammo = value

    # -- Batched unlock tracking (ItemInventory-compatible) -----------------

    def strip_all(self) -> None:
        """Batched zero of every bound weapon's owned flag."""
        if not self.weapons:
            return
        ops = [(w.base + _OFFSET_OWNED_FLAG, 0) for w in self.weapons.values()]
        self.pine.batch_write_int32(ops)
        self._raw_owned = dict.fromkeys(self.weapons, 0)

    def apply_all(self, ap_owned: dict[str, bool]) -> None:
        """Batched write of true AP ownership for every bound weapon."""
        if not self.weapons:
            return
        ops = [
            (w.base + _OFFSET_OWNED_FLAG, 1 if ap_owned.get(name, False) else 0)
            for name, w in self.weapons.items() if name in ap_owned
        ]
        self.pine.batch_write_int32(ops)
        self._raw_owned.update({name: int(bool(value)) for name, value in ap_owned.items() if name in self.weapons})

    def sync(self) -> None:
        """Baseline a newly bound table without inventing pickup events."""
        if self.weapons:
            values = self.pine.batch_read_int32([w.base + _OFFSET_OWNED_FLAG for w in self.weapons.values()])
            self._raw_owned = {name: int(bool(value)) for name, value in zip(self.weapons, values)}

    def check(self) -> list[str]:
        """Batched read of every bound weapon's owned flag, diffed against the last-known state."""
        if not self.weapons:
            return []
        names = list(self.weapons)
        addrs = [self.weapons[name].base + _OFFSET_OWNED_FLAG for name in names]
        values = self.pine.batch_read_int32(addrs)
        changed: list[str] = []
        for name, value in zip(names, values):
            owned = 1 if value else 0
            if owned and not self._raw_owned.get(name):
                changed.append(name)
            self._raw_owned[name] = owned
        return changed

    def check_mods(self) -> list[tuple[str, int]]:
        """Batched read of every bound weapon's 3 mod-slot flags (_OFFSET_MOD_SLOTS), diffed against last-known state."""
        if not self.weapons:
            return []
        changed: list[tuple[str, int]] = []
        for name, w in self.weapons.items():
            prev = self._raw_mods.get(name, [0] * MOD_SLOT_COUNT)
            cur = [self.pine.read_int8(w.base + _OFFSET_MOD_SLOTS + s) for s in range(MOD_SLOT_COUNT)]
            for slot, (p, c) in enumerate(zip(prev, cur)):
                if c and not p:
                    changed.append((name, slot))
            self._raw_mods[name] = cur
        return changed

    # -- Batched ammo I/O (for a future ammo-sync client, and for AP's own
    # ammo-count restore/consumable handling if that's ever added) ----------

    def read_ammo(self) -> dict[str, int]:
        """Batched read of every currently-OWNED weapon's ammo."""
        owned_names = [name for name in self.weapons if self._raw_owned.get(name)]
        if not owned_names:
            return {}
        addrs = [self.weapons[name].base + _OFFSET_CURRENT_AMMO for name in owned_names]
        values = self.pine.batch_read_int32(addrs)
        return dict(zip(owned_names, values))

    def write_ammo(self, ammo: dict[str, int]) -> None:
        """Batched write of ammo values, restricted to weapons that are both currently bound (this case's array) and currently owned -- silently drops anything else rather than raising, since an incoming cross-player ammo-sync payload can legitimately reference a weapon this player hasn't picked up yet on this case."""
        ops = [
            (self.weapons[name].base + _OFFSET_CURRENT_AMMO, value)
            for name, value in ammo.items()
            if name in self.weapons and self._raw_owned.get(name)
        ]
        if ops:
            self.pine.batch_write_int32(ops)

    def __repr__(self) -> str:
        return f"WeaponInventory(weapons={len(self.weapons)})"

from __future__ import annotations

# Location-derived lookups transitively import back into core.weapons, so
# they're built lazily on first use to avoid an import cycle.
_LOC_DATA_LOADED = False
VENDOR_WEAPON_LOC: dict[str, str] = {}
VENDOR_GADGET_LOC: dict[str, str] = {}
WEAPON_INTERNAL_TO_LOCATION: dict[str, str] = {}
GADGET_INTERNAL_TO_LOCATION: dict[str, str] = {}
_MOD_LOC: dict[str, tuple[str, str]] = {}
MOD_INTERNAL_TO_LOCATION: dict[tuple[str, str], str] = {}
_TITAN_LOC: dict[str, str] = {}
TITAN_INTERNAL_TO_LOCATION: dict[str, str] = {}

_SLOT_TO_UNLOCK_ATTR: dict[str, str] = {
    "mod_slot_one": "mod_unlock_one",
    "mod_slot_two": "mod_unlock_two",
    "mod_slot_three": "mod_unlock_three",
}

# (internal_weapon, mod_unlock_attr) -> planet the vendor selling that mod
# lives on. Drives the mod_unlock_N "purchasable" byte, which should only
# read 1 once the player owns the weapon (and, on Challax, the extra
# gadgets below — mirrors rules/challax.py's Polarizer gate).
MOD_UNLOCK_PLANET: dict[tuple[str, str], str] = {}

# Planets whose mod vendor requires extra gadgets beyond owning the weapon
# itself, mirroring that planet's AP access_rule for its mod locations.
MOD_UNLOCK_EXTRA_GADGETS: dict[str, tuple[str, ...]] = {}


def _ensure_loc_data() -> None:
    """Populate the location/item-derived module globals (lazy, idempotent)."""
    global _LOC_DATA_LOADED, VENDOR_WEAPON_LOC, VENDOR_GADGET_LOC
    global WEAPON_INTERNAL_TO_LOCATION, GADGET_INTERNAL_TO_LOCATION
    global _MOD_LOC, MOD_INTERNAL_TO_LOCATION
    global _TITAN_LOC, TITAN_INTERNAL_TO_LOCATION
    global MOD_UNLOCK_PLANET, MOD_UNLOCK_EXTRA_GADGETS
    if _LOC_DATA_LOADED:
        return
    from ...constants import Rac5GadgetKeys, Rac5Planets
    from ...locations import (
        GADGET_INTERNAL_TO_LOCATION as _GADGET_INTERNAL_TO_LOCATION,
        MOD_INTERNAL_TO_LOCATION as _MOD_INTERNAL_TO_LOCATION,
        TITAN_INTERNAL_TO_LOCATION as _TITAN_INTERNAL_TO_LOCATION,
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
    TITAN_INTERNAL_TO_LOCATION = _TITAN_INTERNAL_TO_LOCATION
    _TITAN_LOC = {v: k for k, v in _TITAN_INTERNAL_TO_LOCATION.items()}
    MOD_UNLOCK_PLANET = {
        (weapon, _SLOT_TO_UNLOCK_ATTR[slot]): _WEAPON_MOD_VENDOR_LOCATIONS[loc].region
        for (weapon, slot), loc in _MOD_INTERNAL_TO_LOCATION.items()
    }
    MOD_UNLOCK_EXTRA_GADGETS = {
        Rac5Planets.CHALLAX: (Rac5GadgetKeys.SHRINK_RAY, Rac5GadgetKeys.POLARIZER),
    }
    _LOC_DATA_LOADED = True


def __getattr__(name: str):
    # Resolve the lazily-built location lookups on attribute access.
    if name in (
        "VENDOR_WEAPON_LOC", "VENDOR_GADGET_LOC",
        "WEAPON_INTERNAL_TO_LOCATION", "GADGET_INTERNAL_TO_LOCATION",
        "MOD_INTERNAL_TO_LOCATION", "_MOD_LOC",
        "TITAN_INTERNAL_TO_LOCATION", "_TITAN_LOC",
        "MOD_UNLOCK_PLANET", "MOD_UNLOCK_EXTRA_GADGETS",
    ):
        _ensure_loc_data()
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

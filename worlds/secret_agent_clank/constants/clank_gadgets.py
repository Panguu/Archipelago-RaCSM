"""Clank item names."""
from dataclasses import dataclass

from .planets import CASE_ID_TO_CASE


@dataclass(frozen=True)
class SACClankWeapons:
    """WEAPON_ORDER-struct Clank items that have a progressive counterpart (see SACProgressiveClankWeapons) -- see module docstring for the split from SACClankGadgets' lock/unlock-only items."""
    THROWTIE          = "Tie-A-Rang (Clank)"
    CUFFLINK          = "Cufflink Bomb (Clank)"
    TANGLEVINE        = "Tanglevine Carnation (Clank)"
    FLAMETHROWERPEN   = "Blowtorch Briefcase (Clank)"
    HOLOKNUCKLES      = "Holo-Knuckles (Clank)"
    SUPERKICK         = "Clank Fu Kick (Clank)"
    LIGHTNINGUMBRELLA = "Thunderstorm Umbrella (Clank)"
    KICKSPLOSION      = "Clank Fu Hot Foot (Clank)"


@dataclass(frozen=True)
class SACProgressiveClankWeapons:
    """Progressive-item counterpart to SACClankWeapons."""
    THROWTIE          = "Progressive Tie-A-Rang (Clank)"
    CUFFLINK          = "Progressive Cufflink Bomb (Clank)"
    TANGLEVINE        = "Progressive Tanglevine Carnation (Clank)"
    FLAMETHROWERPEN   = "Progressive Blowtorch Briefcase (Clank)"
    HOLOKNUCKLES      = "Progressive Holo-Knuckles (Clank)"
    SUPERKICK         = "Progressive Clank Fu Kick (Clank)"
    LIGHTNINGUMBRELLA = "Progressive Thunderstorm Umbrella (Clank)"
    KICKSPLOSION      = "Progressive Clank Fu Hot Foot (Clank)"


@dataclass(frozen=True)
class SACClankGadgets:
    """Lock/unlock-only Clank items (no progression) -- see module docstring for why the two mechanically-separate tracking systems (case_id-keyed CLANK_GADGET_BY_CASE_ID vs the shared WEAPON_ORDER struct) share one naming class."""

    BLACK_OUT_PEN      = "Blackout Pen (Clank)"
    THERM_OPTIC_SHADES = "Therm-Optic Shades (Clank)"
    CLANKPDA           = "Agency PDA (Clank)"
    JETBOOTS           = "Jet Boots (Clank)"
    OMNIKEY            = "Omni-Key 5000 (Clank)"
    HYPNOWATCH         = "Hypno-Watch (Clank)"
    HOLOMONOCLE        = "Holo-Monocle (Clank)"
    BOLTGRABBER        = "Bolt Grabber (Clank)"


# Back-compat aliases -- existing callers (rule_helpers.py, regions.py,
# items/__init__.py) import these two flat names directly.
BLACK_OUT_PEN = SACClankGadgets.BLACK_OUT_PEN
THERM_OPTIC_SHADES = SACClankGadgets.THERM_OPTIC_SHADES

# Case_id -> gadget name for the positional (non-WEAPON_ORDER) Clank gadget
# system -- keyed by case_id rather than a plain tuple position so a gap
# (no confirmed gadget at case_id 2/3) doesn't require every later entry to
# shift, unlike the old CLANK_GADGETS tuple this replaces.
CLANK_GADGET_BY_CASE_ID: dict[int, str] = {
    1: SACClankGadgets.BLACK_OUT_PEN,        # Boltaire Museum -- CONFIRMED, see docstring
    4: SACClankGadgets.THERM_OPTIC_SHADES,   # Rooftop Deathtrap
}

# Flat tuple for items/__init__.py's _table() -- iteration order matches
# CLANK_GADGET_BY_CASE_ID's insertion order (Python dicts preserve it).
CLANK_GADGETS: tuple[str, ...] = tuple(CLANK_GADGET_BY_CASE_ID.values())

# Case name -> that case's "{gadget} (Pickup)" location name, derived from
# CLANK_GADGET_BY_CASE_ID above (see locations/<case>.py's identical
# `f"{CLANK_GADGET_BY_CASE_ID[_CASE_ID]} (Pickup)"` construction) -- lets
# rules/<case>.py reference this location by constant instead of
# hand-typing the same string a second time.
GADGET_PICKUP_BY_CASE: dict[str, str] = {
    CASE_ID_TO_CASE[case_id].name: f"{gadget} (Pickup)"
    for case_id, gadget in CLANK_GADGET_BY_CASE_ID.items()
    if case_id in CASE_ID_TO_CASE
}


@dataclass(frozen=True)
class SACGadgetPickupLocations:
    """One named constant per "{gadget} (Pickup)" location -- same values as GADGET_PICKUP_BY_CASE, spelled out here so rules/<case>.py can reference an individual location directly instead of a case-name-keyed lookup -- same one-name-per-location layout as constants/weapons.py's SACRatchetWeapons."""

    BOLTAIRE_MUSEUM = "Boltaire (Clank) - Boltaire Museum: Blackout Pen Pickup"
    ROOFTOP_DEATHTRAP = "Boltaire (Clank) - Boltaire Museum: Therm-Optic Shades Pickup"

assert {v for k, v in vars(SACGadgetPickupLocations).items() if not k.startswith("_")} == set(
    GADGET_PICKUP_BY_CASE.values()
), "SACGadgetPickupLocations drifted out of sync with GADGET_PICKUP_BY_CASE -- regenerate its literals"

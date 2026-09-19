"""Clank item names."""
from dataclasses import dataclass


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
    LIGHTNINGUMBRELLA = "Progressive Thunderstorm Umbrella (Clank)"


@dataclass(frozen=True)
class SACProtoWeapons:
    """Fully-upgraded (NG+ Titan Vendor) counterpart to SACClankWeapons -- only the
    weapons with a Proto tier get a member here, matched by shared attribute name to
    the SACClankWeapons entry it upgrades (see constants/weapon_progression.py)."""
    THROWTIE          = "Proto Tie-A-Rang (Clank)"
    CUFFLINK          = "Proto Cufflink Bomb (Clank)"
    TANGLEVINE        = "Proto Tanglevine Carnation (Clank)"
    FLAMETHROWERPEN   = "Proto Blowtorch Briefcase (Clank)"
    HOLOKNUCKLES      = "Proto Holo-Knuckles (Clank)"
    LIGHTNINGUMBRELLA = "Proto Thunderstorm Umbrella (Clank)"


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


# Case_id -> gadget names for the positional (non-WEAPON_ORDER) Clank gadget
# system -- keyed by case_id rather than a plain tuple position so a gap
# (no confirmed gadget at case_id 2/3) doesn't require every later entry to
# shift, unlike the old CLANK_GADGETS tuple this replaces. Both Black Out Pen
# and Therm-Optic Shades are picked up in Boltaire Museum -- CONFIRMED.
CLANK_GADGET_BY_CASE_ID: dict[int, tuple[str, ...]] = {
    1: (SACClankGadgets.BLACK_OUT_PEN, SACClankGadgets.THERM_OPTIC_SHADES),  # Boltaire Museum
}

# Flat tuple for items/__init__.py's _table() -- iteration order matches
# CLANK_GADGET_BY_CASE_ID's insertion order (Python dicts preserve it).
CLANK_GADGETS: tuple[str, ...] = tuple(
    gadget for gadgets in CLANK_GADGET_BY_CASE_ID.values() for gadget in gadgets
)


def gadget_pickup_name(display_name: str) -> str:
    return f"{display_name} (Pickup)"


@dataclass(frozen=True)
class SACGadgetPickupLocations:
    """Both gadgets are picked up in Boltaire Museum (case_id 1) -- see
    CLANK_GADGET_BY_CASE_ID above -- so both attribute names share that case
    prefix even though there's no second, Rooftop-Deathtrap-only pickup."""
    BOLTAIRE_MUSEUM_BLACK_OUT_PEN = gadget_pickup_name(SACClankGadgets.BLACK_OUT_PEN)
    BOLTAIRE_MUSEUM_THERM_OPTIC_SHADES = gadget_pickup_name(SACClankGadgets.THERM_OPTIC_SHADES)

"""Ratchet's weapons/tools, sourced from the single 40-slot WeaponData struct array core/weapons.py's WEAPON_ORDER documents."""
from dataclasses import dataclass

from .clank_gadgets import SACClankGadgets, SACClankWeapons
from .planets import SACCases
from .weapon_order import WEAPON_ORDER, WeaponSlot


@dataclass(frozen=True)
class SACRatchetWeapons:
    SHOCKROCKET       = "Shock Rocket (Ratchet)"
    PLASMAWHIP        = "Plasma Whip (Ratchet)"
    PORKBOMB          = "Pork Bomb Gun (Ratchet)"
    KICKBLAST         = "Kick Blast (Ratchet)"
    BLASTER           = "Dual Lacerators (Ratchet)"
    SHARDGUN          = "Shard Gun (Ratchet)"
    BEEMINEGLOVE      = "Bee Mine Mk. II (Ratchet)"
    WALLOPER          = "Walloper (Ratchet)"
    MINELAUNCHER      = "Mine Launcher (Ratchet)"
    RATCHETPDA        = "Agency PDA (Ratchet)"
    BOLTTRANSFER      = "Bolt Transfer (Ratchet)"
    RYNO              = "RYNO (Ratchet)"


@dataclass(frozen=True)
class SACProgressiveRatchetWeapons:
    SHOCKROCKET       = "Progressive Shock Rocket (Ratchet)"
    PLASMAWHIP        = "Progressive Plasma Whip (Ratchet)"
    PORKBOMB          = "Progressive Pork Bomb Gun (Ratchet)"
    BLASTER           = "Progressive Dual Lacerators (Ratchet)"
    SHARDGUN          = "Progressive Shard Gun (Ratchet)"
    BEEMINEGLOVE      = "Progressive Bee Mine Mk. II (Ratchet)"
    WALLOPER          = "Progressive Walloper (Ratchet)"
    MINELAUNCHER      = "Progressive Mine Launcher (Ratchet)"
    RATCHETPDA        = "Progressive Agency PDA (Ratchet)"
    BOLTTRANSFER      = "Progressive Bolt Transfer (Ratchet)"
    RYNO              = "Progressive RYNO (Ratchet)"


@dataclass(frozen=True)
class SACQwarkWeapons:
    """We are not including Qwarks weapons in AP tool just for noting"""
    QWARKBLASTER      = "Blaster (Qwark)"
    GIANTQWARKBLASTER = "Giant Blaster (Qwark)"


# Display name -> WEAPON_ORDER internal name (core/weapons.py) -- used by
# core/core.py every tick to translate WeaponInventory.check()'s raw
# results before send_location().
RATCHET_WEAPON_DISPLAY_TO_INTERNAL: dict[str, str] = {
    SACRatchetWeapons.SHOCKROCKET:       WEAPON_ORDER[WeaponSlot.SHOCKROCKET],
    SACRatchetWeapons.PLASMAWHIP:        WEAPON_ORDER[WeaponSlot.PLASMAWHIP],
    SACRatchetWeapons.PORKBOMB:          WEAPON_ORDER[WeaponSlot.PORKBOMB],
    SACRatchetWeapons.KICKBLAST:         WEAPON_ORDER[WeaponSlot.KICKBLAST],
    SACRatchetWeapons.BLASTER:           WEAPON_ORDER[WeaponSlot.BLASTER],
    SACRatchetWeapons.SHARDGUN:          WEAPON_ORDER[WeaponSlot.SHARDGUN],
    SACRatchetWeapons.BEEMINEGLOVE:      WEAPON_ORDER[WeaponSlot.BEEMINEGLOVE],
    SACRatchetWeapons.WALLOPER:          WEAPON_ORDER[WeaponSlot.WALLOPER],
    SACRatchetWeapons.MINELAUNCHER:      WEAPON_ORDER[WeaponSlot.MINELAUNCHER],
    SACRatchetWeapons.RATCHETPDA:        WEAPON_ORDER[WeaponSlot.RATCHETPDA],
    SACRatchetWeapons.BOLTTRANSFER:      WEAPON_ORDER[WeaponSlot.BOLTTRANSFER],
    SACRatchetWeapons.RYNO:              WEAPON_ORDER[WeaponSlot.RYNO],
}
RATCHET_WEAPON_INTERNAL_TO_DISPLAY: dict[str, str] = {v: k for k, v in RATCHET_WEAPON_DISPLAY_TO_INTERNAL.items()}

# WEAPON_ORDER-struct half of Clank's items (constants/clank_gadgets.py) --
# both SACClankGadgets (lock/unlock-only) and SACClankWeapons (has
# progression) combined, since world.py only needs to know "is this
# WEAPON_ORDER slot Clank's", not which of the two naming classes it's in.
GADGET_DISPLAY_TO_INTERNAL: dict[str, str] = {
    SACClankGadgets.CLANKPDA:        WEAPON_ORDER[WeaponSlot.CLANKPDA],
    SACClankGadgets.JETBOOTS:        WEAPON_ORDER[WeaponSlot.JETBOOTS],
    SACClankGadgets.OMNIKEY:         WEAPON_ORDER[WeaponSlot.OMNIKEY],
    SACClankGadgets.HYPNOWATCH:      WEAPON_ORDER[WeaponSlot.HYPNOWATCH],
    SACClankGadgets.HOLOMONOCLE:     WEAPON_ORDER[WeaponSlot.HOLOMONOCLE],
    SACClankGadgets.BOLTGRABBER:     WEAPON_ORDER[WeaponSlot.BOLTGRABBER],
    SACClankWeapons.THROWTIE:          WEAPON_ORDER[WeaponSlot.THROWTIE],
    SACClankWeapons.CUFFLINK:          WEAPON_ORDER[WeaponSlot.CUFFLINK],
    SACClankWeapons.TANGLEVINE:        WEAPON_ORDER[WeaponSlot.TANGLEVINE],
    SACClankWeapons.FLAMETHROWERPEN:   WEAPON_ORDER[WeaponSlot.FLAMETHROWERPEN],
    SACClankWeapons.HOLOKNUCKLES:      WEAPON_ORDER[WeaponSlot.HOLOKNUCKLES],
    SACClankWeapons.SUPERKICK:         WEAPON_ORDER[WeaponSlot.SUPERKICK],
    SACClankWeapons.LIGHTNINGUMBRELLA: WEAPON_ORDER[WeaponSlot.LIGHTNINGUMBRELLA],
    SACClankWeapons.KICKSPLOSION:      WEAPON_ORDER[WeaponSlot.KICKSPLOSION],
}
GADGET_INTERNAL_TO_DISPLAY: dict[str, str] = {v: k for k, v in GADGET_DISPLAY_TO_INTERNAL.items()}

# Both characters use the native GadgetData array. Keep AP names independent
# of its internal slot names; the pen and shades retain separate pickup IDs.
EQUIPMENT_DISPLAY_TO_INTERNAL = {
    **RATCHET_WEAPON_DISPLAY_TO_INTERNAL,
    **GADGET_DISPLAY_TO_INTERNAL,
}
EQUIPMENT_INTERNAL_TO_DISPLAY = {
    internal: display for display, internal in EQUIPMENT_DISPLAY_TO_INTERNAL.items()
}
CLANK_PICKUP_TO_INTERNAL = {
    SACClankGadgets.BLACK_OUT_PEN: "fountainpen",
    SACClankGadgets.THERM_OPTIC_SHADES: "sunglasses",
}


# Flat tuples for items/__init__.py's _table().
RATCHET_WEAPONS: tuple[str, ...] = tuple(RATCHET_WEAPON_DISPLAY_TO_INTERNAL)
GADGETS_FROM_WEAPON_TABLE: tuple[str, ...] = tuple(GADGET_DISPLAY_TO_INTERNAL)

# Mapping of each SACRatchetWeapons entry to the SACCases case its AP
# location lives in.
# STATUS: LOW CONFIDENCE -- expect individual entries to move once verified
# live (e.g. via /force_case + checking what that case's vendor/level offers).
WEAPONS_BY_CASE: dict[str, tuple[str, ...]] = {
    SACCases.BOLTAIRE_MUSEUM: (
        SACRatchetWeapons.BLASTER,
    ),
    SACCases.MAX_SECURITY_CELLS: (
        SACRatchetWeapons.SHARDGUN, SACRatchetWeapons.WALLOPER,
    ),
    SACCases.ROOFTOP_DEATHTRAP: (
        SACRatchetWeapons.MINELAUNCHER,
    ),
    SACCases.AZCOTAL_ALLEY: (
        SACRatchetWeapons.BEEMINEGLOVE,
    ),
    SACCases.HIGH_ROLLERS_CASINO: (
        SACRatchetWeapons.PORKBOMB,
    ),
    SACCases.VENANTONIO_LABS: (
        SACRatchetWeapons.PLASMAWHIP, SACRatchetWeapons.KICKBLAST,
    ),
    SACCases.INSIDE_THE_A_EYE: (
        SACRatchetWeapons.SHOCKROCKET,
    ),
    SACCases.KLUNKS_LAIR: (
        SACRatchetWeapons.RYNO,
    ),
}

# Same shape/confidence caveat as WEAPONS_BY_CASE above, for the Clank
# items that live in this same WEAPON_ORDER struct -- case placements
# carried over unchanged from when these were (mis)classified as Ratchet
# weapons in WEAPONS_BY_CASE, not re-derived.
GADGETS_BY_CASE: dict[str, tuple[str, ...]] = {
    SACCases.BOLTAIRE_MUSEUM: (
        SACClankWeapons.THROWTIE, SACClankGadgets.JETBOOTS,
        SACClankWeapons.HOLOKNUCKLES, SACClankWeapons.SUPERKICK,
        SACClankGadgets.BLACK_OUT_PEN, SACClankGadgets.THERM_OPTIC_SHADES,
    ),
    SACCases.ROOFTOP_DEATHTRAP: (
        SACClankWeapons.CUFFLINK, SACClankGadgets.OMNIKEY,
    ),
    SACCases.AZCOTAL_ALLEY: (
        SACClankWeapons.TANGLEVINE, SACClankGadgets.CLANKPDA,
    ),
    SACCases.HIGH_ROLLERS_CASINO: (
        SACClankGadgets.HYPNOWATCH, SACClankGadgets.HOLOMONOCLE,
    ),
    SACCases.VENANTONIO_LABS: (
        SACClankWeapons.FLAMETHROWERPEN, SACClankWeapons.LIGHTNINGUMBRELLA,
    ),
    SACCases.INSIDE_THE_A_EYE: (
        SACClankGadgets.BOLTGRABBER,
    ),
    SACCases.KLUNKS_LAIR: (
        SACClankWeapons.KICKSPLOSION,
    ),
}

# Reverse of WEAPONS_BY_CASE/GADGETS_BY_CASE -- display name -> the case its
# AP location lives in, so a caller (regions.py's Titan Vendor filtering)
# can tell which case must be active for a given weapon's location to exist.
CASE_BY_WEAPON_NAME: dict[str, str] = {
    name: case_name
    for table in (WEAPONS_BY_CASE, GADGETS_BY_CASE)
    for case_name, names in table.items()
    for name in names
}

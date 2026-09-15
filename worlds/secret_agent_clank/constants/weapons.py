"""Ratchet's weapons/tools, sourced from the single 40-slot WeaponData struct array core/weapons.py's WEAPON_ORDER documents."""
from dataclasses import dataclass

from .clank_gadgets import SACClankGadgets, SACClankWeapons


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
    SACRatchetWeapons.SHOCKROCKET:       "shockrocket",
    SACRatchetWeapons.PLASMAWHIP:        "plasmawhip",
    SACRatchetWeapons.PORKBOMB:          "porkbomb",
    SACRatchetWeapons.KICKBLAST:         "kickblast",
    SACRatchetWeapons.BLASTER:           "blaster",
    SACRatchetWeapons.SHARDGUN:          "shardgun",
    SACRatchetWeapons.BEEMINEGLOVE:      "beemineglove",
    SACRatchetWeapons.WALLOPER:          "walloper",
    SACRatchetWeapons.MINELAUNCHER:      "minelauncher",
    SACRatchetWeapons.RATCHETPDA:        "ratchetpda",
    SACRatchetWeapons.BOLTTRANSFER:      "bolttransfer",
    SACRatchetWeapons.RYNO:              "ryno",
}
RATCHET_WEAPON_INTERNAL_TO_DISPLAY: dict[str, str] = {v: k for k, v in RATCHET_WEAPON_DISPLAY_TO_INTERNAL.items()}

# WEAPON_ORDER-struct half of Clank's items (constants/clank_gadgets.py) --
# both SACClankGadgets (lock/unlock-only) and SACClankWeapons (has
# progression) combined, since world.py only needs to know "is this
# WEAPON_ORDER slot Clank's", not which of the two naming classes it's in.
GADGET_DISPLAY_TO_INTERNAL: dict[str, str] = {
    SACClankGadgets.CLANKPDA:        "clankpda",
    SACClankGadgets.JETBOOTS:        "jetboots",
    SACClankGadgets.OMNIKEY:         "omnikey",
    SACClankGadgets.HYPNOWATCH:      "hypnowatch",
    SACClankGadgets.HOLOMONOCLE:     "holomonocle",
    SACClankGadgets.BOLTGRABBER:     "boltgrabber",
    SACClankWeapons.THROWTIE:          "throwTie",
    SACClankWeapons.CUFFLINK:          "CuffLink",
    SACClankWeapons.TANGLEVINE:        "TangleVine",
    SACClankWeapons.FLAMETHROWERPEN:   "FlamethrowerPen",
    SACClankWeapons.HOLOKNUCKLES:      "HoloKnuckles",
    SACClankWeapons.SUPERKICK:         "superkick",
    SACClankWeapons.LIGHTNINGUMBRELLA: "LightningUmbrella",
    SACClankWeapons.KICKSPLOSION:      "kicksplosion",
}
GADGET_INTERNAL_TO_DISPLAY: dict[str, str] = {v: k for k, v in GADGET_DISPLAY_TO_INTERNAL.items()}

# Flat tuples for items/__init__.py's _table().
RATCHET_WEAPONS: tuple[str, ...] = tuple(RATCHET_WEAPON_DISPLAY_TO_INTERNAL)
GADGETS_FROM_WEAPON_TABLE: tuple[str, ...] = tuple(GADGET_DISPLAY_TO_INTERNAL)

# Mapping of each SACRatchetWeapons entry to the SACCases case its AP
# location lives in.
# STATUS: LOW CONFIDENCE -- expect individual entries to move once verified
# live (e.g. via /force_case + checking what that case's vendor/level offers).
WEAPONS_BY_CASE: dict[str, tuple[str, ...]] = {
    "Boltaire Museum": (
        SACRatchetWeapons.BLASTER,
    ),
    "Max-Security Cells": (
        SACRatchetWeapons.SHARDGUN, SACRatchetWeapons.WALLOPER,
    ),
    "Rooftop Deathtrap": (
        SACRatchetWeapons.MINELAUNCHER,
    ),
    "Azcotal Alley": (
        SACRatchetWeapons.BEEMINEGLOVE,
    ),
    "High-Rollers Casino": (
        SACRatchetWeapons.PORKBOMB,
    ),
    "Venantonio Labs": (
        SACRatchetWeapons.PLASMAWHIP, SACRatchetWeapons.KICKBLAST,
    ),
    "Inside the A-Eye": (
        SACRatchetWeapons.SHOCKROCKET,
    ),
    "Klunk's Lair": (
        SACRatchetWeapons.RYNO,
    ),
}

# Same shape/confidence caveat as WEAPONS_BY_CASE above, for the Clank
# items that live in this same WEAPON_ORDER struct -- case placements
# carried over unchanged from when these were (mis)classified as Ratchet
# weapons in WEAPONS_BY_CASE, not re-derived.
GADGETS_BY_CASE: dict[str, tuple[str, ...]] = {
    "Boltaire Museum": (
        SACClankWeapons.THROWTIE, SACClankGadgets.JETBOOTS,
        SACClankWeapons.HOLOKNUCKLES, SACClankWeapons.SUPERKICK,
    ),
    "Rooftop Deathtrap": (
        SACClankWeapons.CUFFLINK, SACClankGadgets.OMNIKEY,
    ),
    "Azcotal Alley": (
        SACClankWeapons.TANGLEVINE, SACClankGadgets.CLANKPDA,
    ),
    "High-Rollers Casino": (
        SACClankGadgets.HYPNOWATCH, SACClankGadgets.HOLOMONOCLE,
    ),
    "Venantonio Labs": (
        SACClankWeapons.FLAMETHROWERPEN, SACClankWeapons.LIGHTNINGUMBRELLA,
    ),
    "Inside the A-Eye": (
        SACClankGadgets.BOLTGRABBER,
    ),
    "Klunk's Lair": (
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

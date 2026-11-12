"""Only native multi-level weapons participate; tools stay single unlocks.

Roster: https://ratchetandclank.fandom.com/wiki/Secret_Agent_Clank_(game)
Challenge tiers: https://ratchetandclank.fandom.com/wiki/Secret_Agent_Clank_vendors
RYNO V4 cap: https://ratchet-galaxy.com/en/games/psp/secret-agent-clank/inventory/weapons/ryno
Six Clank weapons and nine Ratchet weapons; no PDAs, tools, or Clank Fu moves.
"""
from .clank_gadgets import SACClankWeapons, SACProgressiveClankWeapons, SACProtoWeapons
from .option_choices import WeaponLevelChecksOptions
from .vendor import vendor_location_name
from .weapons import (
    EQUIPMENT_DISPLAY_TO_INTERNAL,
    EQUIPMENT_INTERNAL_TO_DISPLAY,
    SACProgressiveRatchetWeapons,
    SACRatchetWeapons,
    SACTitanWeapons,
)

LEVELLED_INTERNALS = ("blaster", "shardgun", "beemineglove", "shockrocket",
    "walloper", "plasmawhip", "porkbomb", "minelauncher", "ryno", "throwTie",
    "CuffLink", "TangleVine", "HoloKnuckles", "FlamethrowerPen", "LightningUmbrella")


def _counterparts(base, upgraded):
    """Pair explicit names by their shared constant attribute, without parsing names."""
    return (
        (getattr(base, attr), name)
        for attr, name in vars(upgraded).items()
        if not attr.startswith("_") and hasattr(base, attr)
    )


UNLOCK_TO_PROGRESSIVE = {
    unlock: progressive
    for base, upgraded in (
        (SACRatchetWeapons, SACProgressiveRatchetWeapons),
        (SACClankWeapons, SACProgressiveClankWeapons),
    )
    for unlock, progressive in _counterparts(base, upgraded)
    if EQUIPMENT_DISPLAY_TO_INTERNAL[unlock] in LEVELLED_INTERNALS
}
PROGRESSIVE_TO_INTERNAL = {
    progressive: EQUIPMENT_DISPLAY_TO_INTERNAL[unlock] for unlock, progressive in UNLOCK_TO_PROGRESSIVE.items()
}
PROGRESSIVE_TO_UNLOCK = {progressive: unlock for unlock, progressive in UNLOCK_TO_PROGRESSIVE.items()}


def max_level(internal, ng_plus):
    if internal not in LEVELLED_INTERNALS:
        return 1
    return 4 if internal == "ryno" or not ng_plus else 8


def checked_levels(internal, mode, ng_plus):
    """Shared generation/runtime selection, including the RYNO exception."""
    cap = max_level(internal, ng_plus)
    candidates = {
        WeaponLevelChecksOptions.OFF: (),
        WeaponLevelChecksOptions.LEVEL_4: (4,),
        WeaponLevelChecksOptions.LEVEL_8: (8,),
        WeaponLevelChecksOptions.LEVEL_4_AND_8: (4, 8),
        WeaponLevelChecksOptions.ALL: range(2, 9),
    }[mode]
    return tuple(level for level in candidates if level <= cap)


PROGRESSIVE_WRENCH = "Progressive Wrench"

WEAPON_LEVEL_NAME = "Weapon Level: {weapon_name} V{level}"


def level_location_name(internal, level):
    return WEAPON_LEVEL_NAME.format(weapon_name=EQUIPMENT_INTERNAL_TO_DISPLAY[internal], level=level)


_TITAN_EQUIPMENT = tuple(
    (EQUIPMENT_DISPLAY_TO_INTERNAL[unlock], titan)
    for base, upgraded in (
        (SACRatchetWeapons, SACTitanWeapons),
        (SACClankWeapons, SACProtoWeapons),
    )
    for unlock, titan in _counterparts(base, upgraded)
)
TITAN_LOCATIONS = {
    internal: vendor_location_name(titan) for internal, titan in _TITAN_EQUIPMENT
}
TITAN_ITEMS = {
    f"Titan Upgrade: {titan}": internal for internal, titan in _TITAN_EQUIPMENT
}

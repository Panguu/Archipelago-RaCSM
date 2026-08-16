from typing import NamedTuple

from BaseClasses import ItemClassification

from .constants import (
    Rac5Armours,
    Rac5Filler,
    Rac5GadgetKeys,
    Rac5Gadgets,
    Rac5ProgressiveArmours,
    Rac5ProgressiveWeaponMods,
    Rac5ProgressiveWeapons,
    Rac5WeaponKeys,
    Rac5WeaponMods,
    Rac5Weapons,
)
from .core.planets import INFOBOT_ITEM_TO_PLANET
from .core.traps import TRAP_DURATIONS
from .core.weapons import GADGET_DATA, WEAPON_DATA, WEAPON_MAX_LEVELS, WEAPON_MOD_COUNTS

BASE_ID = 77_700_000


class RACItemData(NamedTuple):
    code: int
    classification: ItemClassification


WEAPON_DISPLAY_TO_INTERNAL: dict[str, str] = {
    Rac5Weapons.LACERATOR:       Rac5WeaponKeys.LACERATOR,
    Rac5Weapons.CONCUSSION_GUN:  Rac5WeaponKeys.CONCUSSION_GUN,
    Rac5Weapons.ACID_BOMB_GLOVE: Rac5WeaponKeys.ACID_BOMB_GLOVE,
    Rac5Weapons.AGENTS_OF_DOOM:  Rac5WeaponKeys.AGENTS_OF_DOOM,
    Rac5Weapons.BEE_MINE_GLOVE:  Rac5WeaponKeys.BEE_MINE_GLOVE,
    Rac5Weapons.STATIC_BARRIER:  Rac5WeaponKeys.STATIC_BARRIER,
    Rac5Weapons.SHOCK_ROCKET:    Rac5WeaponKeys.SHOCK_ROCKET,
    Rac5Weapons.SNIPER_MINE:     Rac5WeaponKeys.SNIPER_MINE,
    Rac5Weapons.SCORCHER:        Rac5WeaponKeys.SCORCHER,
    Rac5Weapons.LASER_TRACER:    Rac5WeaponKeys.LASER_TRACER,
    Rac5Weapons.SUCK_CANNON:     Rac5WeaponKeys.SUCK_CANNON,
    Rac5Weapons.MOOTATOR:        Rac5WeaponKeys.MOOTATOR,
    Rac5Weapons.RYNO:            Rac5WeaponKeys.RYNO,
}

GADGET_DISPLAY_TO_INTERNAL: dict[str, str] = {
    Rac5Gadgets.HYPERSHOT:      Rac5GadgetKeys.HYPERSHOT,
    Rac5Gadgets.SPROUT_O_MATIC: Rac5GadgetKeys.SPROUT_O_MATIC,
    Rac5Gadgets.POLARIZER:      Rac5GadgetKeys.POLARIZER,
    Rac5Gadgets.PDA:            Rac5GadgetKeys.PDA,
    Rac5Gadgets.SHRINK_RAY:     Rac5GadgetKeys.SHRINK_RAY,
    Rac5Gadgets.BOLT_GRABBER:   Rac5GadgetKeys.BOLT_GRABBER,
    Rac5Gadgets.MAP_O_MATIC:    Rac5GadgetKeys.MAP_O_MATIC,
    Rac5Gadgets.BOX_BREAKER:    Rac5GadgetKeys.BOX_BREAKER,
}

ARMOUR_DISPLAY_TO_INTERNAL: dict[str, tuple[str, int]] = {
    Rac5Armours.WILDFIRE_CHESTPLATE:     ("wildfire",     0x01),
    Rac5Armours.WILDFIRE_HELMET:         ("wildfire",     0x02),
    Rac5Armours.WILDFIRE_GLOVES:         ("wildfire",     0x04),
    Rac5Armours.WILDFIFE_BOOTS:          ("wildfire",     0x10),
    Rac5Armours.SLUDGE_MK9_CHESTPLATE:   ("sludge",       0x01),
    Rac5Armours.SLUDGE_MK9_HELMET:       ("sludge",       0x02),
    Rac5Armours.SLUDGE_MK9_GLOVES:       ("sludge",       0x04),
    Rac5Armours.SLUDGE_MK9_BOOTS:        ("sludge",       0x10),
    Rac5Armours.CRYSTALLIX_CHESTPLATE:   ("crystallix",   0x01),
    Rac5Armours.CRYSTALLIX_HELMET:       ("crystallix",   0x02),
    Rac5Armours.CRYSTALLIX_GLOVES:       ("crystallix",   0x04),
    Rac5Armours.CRYSTALLIX_BOOTS:        ("crystallix",   0x10),
    Rac5Armours.ELECTROSHOCK_CHESTPLATE: ("electroshock", 0x01),
    Rac5Armours.ELECTROSHOCK_HELMET:     ("electroshock", 0x02),
    Rac5Armours.ELECTROSHOCK_GLOVES:     ("electroshock", 0x04),
    Rac5Armours.ELECTROSHOCK_BOOTS:      ("electroshock", 0x10),
    Rac5Armours.MEGA_BOMB_CHESTPLATE:    ("mega_bomb",    0x01),
    Rac5Armours.MEGA_BOMB_HELMET:        ("mega_bomb",    0x02),
    Rac5Armours.MEGA_BOMB_GLOVES:        ("mega_bomb",    0x04),
    Rac5Armours.MEGA_BOMB_BOOTS:         ("mega_bomb",    0x10),
    Rac5Armours.HYPERBOREAN_CHESTPLATE:  ("hyperborean",  0x01),
    Rac5Armours.HYPERBOREAN_HELMET:      ("hyperborean",  0x02),
    Rac5Armours.HYPERBOREAN_GLOVES:      ("hyperborean",  0x04),
    Rac5Armours.HYPERBOREAN_BOOTS:       ("hyperborean",  0x10),
    Rac5Armours.CHAMELEON_CHESTPLATE:    ("chameleon",    0x01),
    Rac5Armours.CHAMELEON_HELMET:        ("chameleon",    0x02),
    Rac5Armours.CHAMELEON_GLOVES:        ("chameleon",    0x04),
    Rac5Armours.CHAMELEON_BOOTS:         ("chameleon",    0x10),
}

# NG+ Items option (options.py's NgPlusItems): with it off, RYNO and the
# Chameleon/Hyperborean armour sets are excluded from the pool. world.py,
# rules/weapon_levels.py, rules/armour_sets.py, and regions.py must all
# agree on this same exclusion.
NG_PLUS_WEAPONS: frozenset[str] = frozenset({Rac5Weapons.RYNO})
NG_PLUS_ARMOUR_SETS: frozenset[str] = frozenset({"hyperborean", "chameleon"})

# Challenge Mode weapon mods: real vendor-purchase locations only exist for
# these (see rules/challenge_mode.py + regions.py), but like RYNO/Hyperborean/
# Chameleon above, they're only ever placed in the pool at all when NG+ Items
# is on.
NG_PLUS_WEAPON_MODS: frozenset[str] = frozenset({
    Rac5WeaponMods.AGENTS_OF_DOOM_MOD_EXPLOSIVE,
    Rac5WeaponMods.SCORCHER_MOD_SUNFLARE,
    Rac5WeaponMods.SUCK_CANNON_MOD_BOUNCE,
    Rac5WeaponMods.BEE_MINE_GLOVE_MOD_HIVE_BOMB,
    Rac5WeaponMods.SNIPER_MINE_MOD_SMART_REFLECTOR,
    Rac5WeaponMods.SHOCK_ROCKET_MOD_MULTI_LAUNCHER,
    Rac5WeaponMods.STATIC_BARRIER_MOD_REFLECTION,
    Rac5WeaponMods.STATIC_BARRIER_MOD_MIRAGE,
    Rac5WeaponMods.LASER_TRACER_MOD_PIERCE,
    Rac5WeaponMods.LASER_TRACER_MOD_RICOCHET,
})

WEAPON_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(BASE_ID + idx, WEAPON_DATA[internal].classification)
    for idx, (name, internal) in enumerate(WEAPON_DISPLAY_TO_INTERNAL.items(), start=1)
}

# Steps for the "Progressive {Weapon}" item: 1 copy unlocks the weapon, each
# subsequent copy grants the next level up.
WEAPON_PROGRESSIVE_STEPS: dict[str, int] = {
    display: 1 + max(0, WEAPON_MAX_LEVELS.get(internal, 1) - 1)
    for display, internal in WEAPON_DISPLAY_TO_INTERNAL.items()
}

PROGRESSIVE_WEAPON_NAME: dict[str, str] = {
    Rac5Weapons.LACERATOR:       Rac5ProgressiveWeapons.LACERATOR,
    Rac5Weapons.CONCUSSION_GUN:  Rac5ProgressiveWeapons.CONCUSSION_GUN,
    Rac5Weapons.ACID_BOMB_GLOVE: Rac5ProgressiveWeapons.ACID_BOMB_GLOVE,
    Rac5Weapons.AGENTS_OF_DOOM:  Rac5ProgressiveWeapons.AGENTS_OF_DOOM,
    Rac5Weapons.BEE_MINE_GLOVE:  Rac5ProgressiveWeapons.BEE_MINE_GLOVE,
    Rac5Weapons.STATIC_BARRIER:  Rac5ProgressiveWeapons.STATIC_BARRIER,
    Rac5Weapons.SHOCK_ROCKET:    Rac5ProgressiveWeapons.SHOCK_ROCKET,
    Rac5Weapons.SNIPER_MINE:     Rac5ProgressiveWeapons.SNIPER_MINE,
    Rac5Weapons.SCORCHER:        Rac5ProgressiveWeapons.SCORCHER,
    Rac5Weapons.LASER_TRACER:    Rac5ProgressiveWeapons.LASER_TRACER,
    Rac5Weapons.SUCK_CANNON:     Rac5ProgressiveWeapons.SUCK_CANNON,
    Rac5Weapons.MOOTATOR:        Rac5ProgressiveWeapons.MOOTATOR,
    Rac5Weapons.RYNO:            Rac5ProgressiveWeapons.RYNO,
}

WEAPON_PROGRESSIVE_ITEM_TABLE: dict[str, RACItemData] = {
    PROGRESSIVE_WEAPON_NAME[display]: RACItemData(BASE_ID + 350 + idx, ItemClassification.progression)
    for idx, display in enumerate(WEAPON_DISPLAY_TO_INTERNAL)
}

# Weapons with at least one mod slot (suck_cannon/mootator/ryno have none).
_WEAPONS_WITH_MODS: list[str] = [
    display for display, internal in WEAPON_DISPLAY_TO_INTERNAL.items()
    if WEAPON_MOD_COUNTS.get(internal, 0) > 0
]

PROGRESSIVE_MOD_NAME: dict[str, str] = {
    Rac5Weapons.LACERATOR:       Rac5ProgressiveWeaponMods.LACERATOR,
    Rac5Weapons.CONCUSSION_GUN:  Rac5ProgressiveWeaponMods.CONCUSSION_GUN,
    Rac5Weapons.ACID_BOMB_GLOVE: Rac5ProgressiveWeaponMods.ACID_BOMB_GLOVE,
    Rac5Weapons.AGENTS_OF_DOOM:  Rac5ProgressiveWeaponMods.AGENTS_OF_DOOM,
    Rac5Weapons.BEE_MINE_GLOVE:  Rac5ProgressiveWeaponMods.BEE_MINE_GLOVE,
    Rac5Weapons.STATIC_BARRIER:  Rac5ProgressiveWeaponMods.STATIC_BARRIER,
    Rac5Weapons.SHOCK_ROCKET:    Rac5ProgressiveWeaponMods.SHOCK_ROCKET,
    Rac5Weapons.SNIPER_MINE:     Rac5ProgressiveWeaponMods.SNIPER_MINE,
    Rac5Weapons.SCORCHER:        Rac5ProgressiveWeaponMods.SCORCHER,
    Rac5Weapons.LASER_TRACER:    Rac5ProgressiveWeaponMods.LASER_TRACER,
    Rac5Weapons.SUCK_CANNON:     Rac5ProgressiveWeaponMods.SUCK_CANNON,
}

# One "Progressive {Weapon} Mod" item per mod slot — each additional copy
# unlocks the next mod slot, independent of the weapon's unlock/level item.
WEAPON_PROGRESSIVE_MOD_ITEM_TABLE: dict[str, RACItemData] = {
    PROGRESSIVE_MOD_NAME[display]: RACItemData(BASE_ID + 380 + idx, ItemClassification.useful)
    for idx, display in enumerate(_WEAPONS_WITH_MODS)
}

# Named mod item per mod slot, in slot order, used when Progressive Mods is off —
# one item per mod slot, each independently grants that specific slot.
WEAPON_MOD_SLOT_NAMES: dict[str, list[str]] = {
    Rac5Weapons.LACERATOR: [
        Rac5WeaponMods.LACERATOR_MOD_LOCK_ON,
        Rac5WeaponMods.LACERATOR_MOD_DOUBLE_BARREL,
    ],
    Rac5Weapons.CONCUSSION_GUN: [
        Rac5WeaponMods.CONCUSSION_GUN_MOD_SPLIT_BARREL,
        Rac5WeaponMods.CONCUSSION_GUN_MOD_LOCK_ON,
        Rac5WeaponMods.CONCUSSION_GUN_MOD_CHARGE_UP,
    ],
    Rac5Weapons.ACID_BOMB_GLOVE: [
        Rac5WeaponMods.ACID_BOMB_GLOVE_MOD_ACID_BOMB,
        Rac5WeaponMods.ACID_BOMB_GLOVE_MOD_EPOXY,
    ],
    # Launcher (normal) before Explosive (Challenge Mode only) — Progressive
    # Mod items unlock slots in this list order, so the non-NG+ mod must
    # come first or a reduced (NG+-off) copy count would unlock the wrong one.
    Rac5Weapons.AGENTS_OF_DOOM: [
        Rac5WeaponMods.AGENTS_OF_DOOM_MOD_LAUNCHER,
        Rac5WeaponMods.AGENTS_OF_DOOM_MOD_EXPLOSIVE,
    ],
    Rac5Weapons.BEE_MINE_GLOVE: [
        Rac5WeaponMods.BEE_MINE_GLOVE_MOD_WORKER,
        Rac5WeaponMods.BEE_MINE_GLOVE_MOD_HIVE_BOMB,
    ],
    Rac5Weapons.STATIC_BARRIER: [
        Rac5WeaponMods.STATIC_BARRIER_MOD_REFLECTION,
        Rac5WeaponMods.STATIC_BARRIER_MOD_MIRAGE,
    ],
    Rac5Weapons.SHOCK_ROCKET: [
        Rac5WeaponMods.SHOCK_ROCKET_MOD_AFTER_SHOCK,
        Rac5WeaponMods.SHOCK_ROCKET_MOD_MULTI_LAUNCHER,
        Rac5WeaponMods.SHOCK_ROCKET_MOD_LOCK_ON,
    ],
    Rac5Weapons.SNIPER_MINE: [
        Rac5WeaponMods.SNIPER_MINE_MOD_SPLIT_BEAM,
        Rac5WeaponMods.SNIPER_MINE_MOD_SMART_REFLECTOR,
    ],
    Rac5Weapons.SCORCHER: [
        Rac5WeaponMods.SCORCHER_MOD_SPLIT_FIRE,
        Rac5WeaponMods.SCORCHER_MOD_SUNFLARE,
    ],
    Rac5Weapons.LASER_TRACER: [
        Rac5WeaponMods.LASER_TRACER_MOD_PIERCE,
        Rac5WeaponMods.LASER_TRACER_MOD_RICOCHET,
    ],
    # Challenge Mode only — Suck Cannon has no mod in vanilla.
    Rac5Weapons.SUCK_CANNON: [
        Rac5WeaponMods.SUCK_CANNON_MOD_BOUNCE,
    ],
}

WEAPON_MOD_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(BASE_ID + 700 + idx, ItemClassification.useful)
    for idx, (display, i, name) in enumerate(
        (display, i, name)
        for display in _WEAPONS_WITH_MODS
        for i, name in enumerate(WEAPON_MOD_SLOT_NAMES[display], start=1)
    )
}

# mod item name -> (weapon display name, 1-indexed slot number)
WEAPON_MOD_NAME_TO_SLOT: dict[str, tuple[str, int]] = {
    name: (display, i)
    for display in _WEAPONS_WITH_MODS
    for i, name in enumerate(WEAPON_MOD_SLOT_NAMES[display], start=1)
}

# internal weapon key -> count of that weapon's mods gated behind NG+ Items
# (the Challenge Mode subset of NG_PLUS_WEAPON_MODS) — world.py subtracts
# this from WEAPON_MOD_COUNTS when sizing each weapon's Progressive Mod item
# count with NG+ Items off, since a Progressive Mod item is one item per
# weapon (not per individual mod).
WEAPON_NG_PLUS_MOD_COUNTS: dict[str, int] = {
    WEAPON_DISPLAY_TO_INTERNAL[display]: sum(1 for name in mods if name in NG_PLUS_WEAPON_MODS)
    for display, mods in WEAPON_MOD_SLOT_NAMES.items()
}


GADGET_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(BASE_ID + 100 + idx, GADGET_DATA[internal].classification)
    for idx, (name, internal) in enumerate(GADGET_DISPLAY_TO_INTERNAL.items(), start=1)
}

ARMOUR_SETS: list[tuple[str, str]] = [
    ("Wildfire",     "wildfire"),
    ("Sludge Mk9",   "sludge"),
    ("Crystallix",   "crystallix"),
    ("Electroshock", "electroshock"),
    ("Mega Bomb",    "mega_bomb"),
    ("Hyperborean",  "hyperborean"),
    ("Chameleon",    "chameleon"),
]

ARMOUR_SET_DISPLAY_TO_INTERNAL: dict[str, str] = dict(ARMOUR_SETS)

ARMOUR_PIECE_BITMASKS: tuple[int, ...] = (0x01, 0x02, 0x04, 0x10)


ARMOUR_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(BASE_ID + 200 + idx, ItemClassification.useful)
    for idx, name in enumerate(ARMOUR_DISPLAY_TO_INTERNAL, start=1)
}

PROGRESSIVE_ARMOUR_NAME: dict[str, str] = {
    "Wildfire":     Rac5ProgressiveArmours.PROGRESSIVE_WILDFIRE,
    "Sludge Mk9":   Rac5ProgressiveArmours.PROGRESSIVE_SLUDGE_MK9,
    "Crystallix":   Rac5ProgressiveArmours.PROGRESSIVE_CRYSTALLIX,
    "Electroshock": Rac5ProgressiveArmours.PROGRESSIVE_ELECTROSHOCK,
    "Mega Bomb":    Rac5ProgressiveArmours.PROGRESSIVE_MEGA_BOMB,
    "Hyperborean":  Rac5ProgressiveArmours.PROGRESSIVE_HYPERBOREAN,
    "Chameleon":    Rac5ProgressiveArmours.PROGRESSIVE_CHAMELEON,
}

ARMOUR_PROGRESSIVE_ITEM_TABLE: dict[str, RACItemData] = {
    PROGRESSIVE_ARMOUR_NAME[display]: RACItemData(BASE_ID + 370 + idx, ItemClassification.useful)
    for idx, (display, _) in enumerate(ARMOUR_SETS)
}

FILLER_ITEM_TABLE: dict[str, RACItemData] = {
    Rac5Filler.BOLTS: RACItemData(BASE_ID + 400, ItemClassification.filler),
}

INFOBOT_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(BASE_ID + 500 + idx, ItemClassification.progression)
    for idx, name in enumerate(INFOBOT_ITEM_TO_PLANET, start=1)
}

TRAP_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(BASE_ID + 600 + idx, ItemClassification.trap)
    for idx, name in enumerate(TRAP_DURATIONS, start=1)
}

# Virtual item for Universal Tracker's glitched-logic sweep only (see
# world.glitches_item_name / worlds/tracker/TrackerCore.py) — collected into
# a separate alternate-reachability state UT uses purely for its own
# glitched-location highlighting. Never added to create_items()'s real pool,
# so it can never appear in an actual seed; still needs a registered
# code/classification here since UT creates it via the normal
# multiworld.create_item() path.
GLITCHES_ITEM_NAME = "Glitches"
GLITCHES_ITEM_TABLE: dict[str, RACItemData] = {
    # +900, not +700: WEAPON_MOD_ITEM_TABLE already starts at BASE_ID + 700
    # (its enumerate() starts at 0), so +700 collided with Suck Cannon's mod.
    GLITCHES_ITEM_NAME: RACItemData(BASE_ID + 900, ItemClassification.progression),
}

ALL_ITEMS: dict[str, RACItemData] = {
    **WEAPON_ITEM_TABLE,
    **GADGET_ITEM_TABLE,
    **ARMOUR_ITEM_TABLE,
    **WEAPON_PROGRESSIVE_ITEM_TABLE,
    **WEAPON_PROGRESSIVE_MOD_ITEM_TABLE,
    **WEAPON_MOD_ITEM_TABLE,
    **ARMOUR_PROGRESSIVE_ITEM_TABLE,
    **INFOBOT_ITEM_TABLE,
    **FILLER_ITEM_TABLE,
    **TRAP_ITEM_TABLE,
    **GLITCHES_ITEM_TABLE,
}

ITEM_ID_TO_NAME: dict[int, str] = {data.code: name for name, data in ALL_ITEMS.items()}

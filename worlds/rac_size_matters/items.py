from typing import NamedTuple

from BaseClasses import ItemClassification

from .constants import RACSMGADGETKEY, RACSMITEM, RACSMWEAPONKEY
from .core.planets import INFOBOT_ITEM_TO_PLANET
from .core.traps import TRAP_DURATIONS
from .core.weapons import GADGET_DATA, WEAPON_DATA, WEAPON_MAX_LEVELS, WEAPON_MOD_COUNTS

BASE_ID = 77_700_000


class RACItemData(NamedTuple):
    code: int
    classification: ItemClassification


WEAPON_DISPLAY_TO_INTERNAL: dict[str, str] = {
    RACSMITEM.LACERATOR:       RACSMWEAPONKEY.LACERATOR,
    RACSMITEM.CONCUSSION_GUN:  RACSMWEAPONKEY.CONCUSSION_GUN,
    RACSMITEM.ACID_BOMB_GLOVE: RACSMWEAPONKEY.ACID_BOMB_GLOVE,
    RACSMITEM.AGENTS_OF_DOOM:  RACSMWEAPONKEY.AGENTS_OF_DOOM,
    RACSMITEM.BEE_MINE_GLOVE:  RACSMWEAPONKEY.BEE_MINE_GLOVE,
    RACSMITEM.STATIC_BARRIER:  RACSMWEAPONKEY.STATIC_BARRIER,
    RACSMITEM.SHOCK_ROCKET:    RACSMWEAPONKEY.SHOCK_ROCKET,
    RACSMITEM.SNIPER_MINE:     RACSMWEAPONKEY.SNIPER_MINE,
    RACSMITEM.SCORCHER:        RACSMWEAPONKEY.SCORCHER,
    RACSMITEM.LASER_TRACER:    RACSMWEAPONKEY.LASER_TRACER,
    RACSMITEM.SUCK_CANNON:     RACSMWEAPONKEY.SUCK_CANNON,
    RACSMITEM.MOOTATOR:        RACSMWEAPONKEY.MOOTATOR,
    RACSMITEM.RYNO:            RACSMWEAPONKEY.RYNO,
}

GADGET_DISPLAY_TO_INTERNAL: dict[str, str] = {
    RACSMITEM.HYPERSHOT:      RACSMGADGETKEY.HYPERSHOT,
    RACSMITEM.SPROUT_O_MATIC: RACSMGADGETKEY.SPROUT_O_MATIC,
    RACSMITEM.POLARIZER:      RACSMGADGETKEY.POLARIZER,
    RACSMITEM.PDA:            RACSMGADGETKEY.PDA,
    RACSMITEM.SHRINK_RAY:     RACSMGADGETKEY.SHRINK_RAY,
    RACSMITEM.BOLT_GRABBER:   RACSMGADGETKEY.BOLT_GRABBER,
    RACSMITEM.MAP_O_MATIC:    RACSMGADGETKEY.MAP_O_MATIC,
    RACSMITEM.BOX_BREAKER:    RACSMGADGETKEY.BOX_BREAKER,
}

ARMOUR_DISPLAY_TO_INTERNAL: dict[str, tuple[str, int]] = {
    RACSMITEM.WILDFIRE_CHESTPLATE:     ("wildfire",     0x01),
    RACSMITEM.WILDFIRE_HELMET:         ("wildfire",     0x02),
    RACSMITEM.WILDFIRE_GLOVES:         ("wildfire",     0x04),
    RACSMITEM.WILDFIFE_BOOTS:          ("wildfire",     0x10),
    RACSMITEM.SLUDGE_MK9_CHESTPLATE:   ("sludge",       0x01),
    RACSMITEM.SLUDGE_MK9_HELMET:       ("sludge",       0x02),
    RACSMITEM.SLUDGE_MK9_GLOVES:       ("sludge",       0x04),
    RACSMITEM.SLUDGE_MK9_BOOTS:        ("sludge",       0x10),
    RACSMITEM.CRYSTALLIX_CHESTPLATE:   ("crystallix",   0x01),
    RACSMITEM.CRYSTALLIX_HELMET:       ("crystallix",   0x02),
    RACSMITEM.CRYSTALLIX_GLOVES:       ("crystallix",   0x04),
    RACSMITEM.CRYSTALLIX_BOOTS:        ("crystallix",   0x10),
    RACSMITEM.ELECTROSHOCK_CHESTPLATE: ("electroshock", 0x01),
    RACSMITEM.ELECTROSHOCK_HELMET:     ("electroshock", 0x02),
    RACSMITEM.ELECTROSHOCK_GLOVES:     ("electroshock", 0x04),
    RACSMITEM.ELECTROSHOCK_BOOTS:      ("electroshock", 0x10),
    RACSMITEM.MEGA_BOMB_CHESTPLATE:    ("mega_bomb",    0x01),
    RACSMITEM.MEGA_BOMB_HELMET:        ("mega_bomb",    0x02),
    RACSMITEM.MEGA_BOMB_GLOVES:        ("mega_bomb",    0x04),
    RACSMITEM.MEGA_BOMB_BOOTS:         ("mega_bomb",    0x10),
    RACSMITEM.HYPERBOREAN_CHESTPLATE:  ("hyperborean",  0x01),
    RACSMITEM.HYPERBOREAN_HELMET:      ("hyperborean",  0x02),
    RACSMITEM.HYPERBOREAN_GLOVES:      ("hyperborean",  0x04),
    RACSMITEM.HYPERBOREAN_BOOTS:       ("hyperborean",  0x10),
    RACSMITEM.CHAMELEON_CHESTPLATE:    ("chameleon",    0x01),
    RACSMITEM.CHAMELEON_HELMET:        ("chameleon",    0x02),
    RACSMITEM.CHAMELEON_GLOVES:        ("chameleon",    0x04),
    RACSMITEM.CHAMELEON_BOOTS:         ("chameleon",    0x10),
}

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
    RACSMITEM.LACERATOR:       RACSMITEM.PROGRESSIVE_LACERATOR,
    RACSMITEM.CONCUSSION_GUN:  RACSMITEM.PROGRESSIVE_CONCUSSION_GUN,
    RACSMITEM.ACID_BOMB_GLOVE: RACSMITEM.PROGRESSIVE_ACID_BOMB_GLOVE,
    RACSMITEM.AGENTS_OF_DOOM:  RACSMITEM.PROGRESSIVE_AGENTS_OF_DOOM,
    RACSMITEM.BEE_MINE_GLOVE:  RACSMITEM.PROGRESSIVE_BEE_MINE_GLOVE,
    RACSMITEM.STATIC_BARRIER:  RACSMITEM.PROGRESSIVE_STATIC_BARRIER,
    RACSMITEM.SHOCK_ROCKET:    RACSMITEM.PROGRESSIVE_SHOCK_ROCKET,
    RACSMITEM.SNIPER_MINE:     RACSMITEM.PROGRESSIVE_SNIPER_MINE,
    RACSMITEM.SCORCHER:        RACSMITEM.PROGRESSIVE_SCORCHER,
    RACSMITEM.LASER_TRACER:    RACSMITEM.PROGRESSIVE_LASER_TRACER,
    RACSMITEM.SUCK_CANNON:     RACSMITEM.PROGRESSIVE_SUCK_CANNON,
    RACSMITEM.MOOTATOR:        RACSMITEM.PROGRESSIVE_MOOTATOR,
    RACSMITEM.RYNO:            RACSMITEM.PROGRESSIVE_RYNO,
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
    RACSMITEM.LACERATOR:       RACSMITEM.PROGRESSIVE_LACERATOR_MOD,
    RACSMITEM.CONCUSSION_GUN:  RACSMITEM.PROGRESSIVE_CONCUSSION_GUN_MOD,
    RACSMITEM.ACID_BOMB_GLOVE: RACSMITEM.PROGRESSIVE_ACID_BOMB_GLOVE_MOD,
    RACSMITEM.AGENTS_OF_DOOM:  RACSMITEM.PROGRESSIVE_AGENTS_OF_DOOM_MOD,
    RACSMITEM.BEE_MINE_GLOVE:  RACSMITEM.PROGRESSIVE_BEE_MINE_GLOVE_MOD,
    RACSMITEM.STATIC_BARRIER:  RACSMITEM.PROGRESSIVE_STATIC_BARRIER_MOD,
    RACSMITEM.SHOCK_ROCKET:    RACSMITEM.PROGRESSIVE_SHOCK_ROCKET_MOD,
    RACSMITEM.SNIPER_MINE:     RACSMITEM.PROGRESSIVE_SNIPER_MINE_MOD,
    RACSMITEM.SCORCHER:        RACSMITEM.PROGRESSIVE_SCORCHER_MOD,
    RACSMITEM.LASER_TRACER:    RACSMITEM.PROGRESSIVE_LASER_TRACER_MOD,
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
    RACSMITEM.LACERATOR: [
        RACSMITEM.LACERATOR_MOD_LOCK_ON,
        RACSMITEM.LACERATOR_MOD_DOUBLE_BARREL,
    ],
    RACSMITEM.CONCUSSION_GUN: [
        RACSMITEM.CONCUSSION_GUN_MOD_SPLIT_BARREL,
        RACSMITEM.CONCUSSION_GUN_MOD_LOCK_ON,
        RACSMITEM.CONCUSSION_GUN_MOD_CHARGE_UP,
    ],
    RACSMITEM.ACID_BOMB_GLOVE: [
        RACSMITEM.ACID_BOMB_GLOVE_MOD_ACID_BOMB,
        RACSMITEM.ACID_BOMB_GLOVE_MOD_EPOXY,
    ],
    RACSMITEM.AGENTS_OF_DOOM: [
        RACSMITEM.AGENTS_OF_DOOM_MOD_LAUNCHER,
        RACSMITEM.AGENTS_OF_DOOM_MOD_EXPLOSIVE,
    ],
    RACSMITEM.BEE_MINE_GLOVE: [
        RACSMITEM.BEE_MINE_GLOVE_MOD_WORKER,
        RACSMITEM.BEE_MINE_GLOVE_MOD_HIVE_BOMB,
    ],
    RACSMITEM.STATIC_BARRIER: [
        RACSMITEM.STATIC_BARRIER_MOD_REFLECTION,
        RACSMITEM.STATIC_BARRIER_MOD_MIRAGE,
    ],
    RACSMITEM.SHOCK_ROCKET: [
        RACSMITEM.SHOCK_ROCKET_MOD_LOCK_ON,
        RACSMITEM.SHOCK_ROCKET_MOD_AFTER_SHOCK,
        RACSMITEM.SHOCK_ROCKET_MOD_MULTI_LAUNCHER,
    ],
    RACSMITEM.SNIPER_MINE: [
        RACSMITEM.SNIPER_MINE_MOD_SPLIT_BEAM,
        RACSMITEM.SNIPER_MINE_MOD_SMART_REFLECTOR,
    ],
    RACSMITEM.SCORCHER: [
        RACSMITEM.SCORCHER_MOD_SPLIT_FIRE,
        RACSMITEM.SCORCHER_MOD_SUNFLARE,
    ],
    RACSMITEM.LASER_TRACER: [
        RACSMITEM.LASER_TRACER_MOD_PIERCE,
        RACSMITEM.LASER_TRACER_MOD_RICOCHET,
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
    "Wildfire":     RACSMITEM.PROGRESSIVE_WILDFIRE,
    "Sludge Mk9":   RACSMITEM.PROGRESSIVE_SLUDGE_MK9,
    "Crystallix":   RACSMITEM.PROGRESSIVE_CRYSTALLIX,
    "Electroshock": RACSMITEM.PROGRESSIVE_ELECTROSHOCK,
    "Mega Bomb":    RACSMITEM.PROGRESSIVE_MEGA_BOMB,
    "Hyperborean":  RACSMITEM.PROGRESSIVE_HYPERBOREAN,
    "Chameleon":    RACSMITEM.PROGRESSIVE_CHAMELEON,
}

ARMOUR_PROGRESSIVE_ITEM_TABLE: dict[str, RACItemData] = {
    PROGRESSIVE_ARMOUR_NAME[display]: RACItemData(BASE_ID + 370 + idx, ItemClassification.useful)
    for idx, (display, _) in enumerate(ARMOUR_SETS)
}

FILLER_ITEM_TABLE: dict[str, RACItemData] = {
    RACSMITEM.BOLTS: RACItemData(BASE_ID + 400, ItemClassification.filler),
}

INFOBOT_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(BASE_ID + 500 + idx, ItemClassification.progression)
    for idx, name in enumerate(INFOBOT_ITEM_TO_PLANET, start=1)
}

TRAP_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(BASE_ID + 600 + idx, ItemClassification.trap)
    for idx, name in enumerate(TRAP_DURATIONS, start=1)
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
}

ITEM_ID_TO_NAME: dict[int, str] = {data.code: name for name, data in ALL_ITEMS.items()}

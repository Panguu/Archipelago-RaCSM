from __future__ import annotations

from ...constants import Rac5WeaponKeys, Rac5WeaponLevels

# (internal weapon key) -> {level -> location name}, referencing the
# Rac5WeaponLevels constants directly by name rather than building the
# attribute name dynamically (e.g. getattr(Rac5WeaponLevels,
# f"{internal.upper()}_LEVEL_{level}")) — explicit here so a typo/rename
# is a NameError at import time, not a silent AttributeError wherever the
# dynamic lookup happened to first run.
WEAPON_LEVEL_NAMES: dict[str, dict[int, str]] = {
    Rac5WeaponKeys.LACERATOR: {
        2: Rac5WeaponLevels.LACERATOR_LEVEL_2,
        3: Rac5WeaponLevels.LACERATOR_LEVEL_3,
        4: Rac5WeaponLevels.LACERATOR_LEVEL_4,
    },
    Rac5WeaponKeys.CONCUSSION_GUN: {
        2: Rac5WeaponLevels.CONCUSSION_GUN_LEVEL_2,
        3: Rac5WeaponLevels.CONCUSSION_GUN_LEVEL_3,
        4: Rac5WeaponLevels.CONCUSSION_GUN_LEVEL_4,
    },
    Rac5WeaponKeys.ACID_BOMB_GLOVE: {
        2: Rac5WeaponLevels.ACID_BOMB_GLOVE_LEVEL_2,
        3: Rac5WeaponLevels.ACID_BOMB_GLOVE_LEVEL_3,
        4: Rac5WeaponLevels.ACID_BOMB_GLOVE_LEVEL_4,
    },
    Rac5WeaponKeys.AGENTS_OF_DOOM: {
        2: Rac5WeaponLevels.AGENTS_OF_DOOM_LEVEL_2,
        3: Rac5WeaponLevels.AGENTS_OF_DOOM_LEVEL_3,
        4: Rac5WeaponLevels.AGENTS_OF_DOOM_LEVEL_4,
    },
    Rac5WeaponKeys.BEE_MINE_GLOVE: {
        2: Rac5WeaponLevels.BEE_MINE_GLOVE_LEVEL_2,
        3: Rac5WeaponLevels.BEE_MINE_GLOVE_LEVEL_3,
        4: Rac5WeaponLevels.BEE_MINE_GLOVE_LEVEL_4,
    },
    Rac5WeaponKeys.STATIC_BARRIER: {
        2: Rac5WeaponLevels.STATIC_BARRIER_LEVEL_2,
        3: Rac5WeaponLevels.STATIC_BARRIER_LEVEL_3,
        4: Rac5WeaponLevels.STATIC_BARRIER_LEVEL_4,
    },
    Rac5WeaponKeys.SHOCK_ROCKET: {
        2: Rac5WeaponLevels.SHOCK_ROCKET_LEVEL_2,
        3: Rac5WeaponLevels.SHOCK_ROCKET_LEVEL_3,
        4: Rac5WeaponLevels.SHOCK_ROCKET_LEVEL_4,
    },
    Rac5WeaponKeys.SNIPER_MINE: {
        2: Rac5WeaponLevels.SNIPER_MINE_LEVEL_2,
        3: Rac5WeaponLevels.SNIPER_MINE_LEVEL_3,
        4: Rac5WeaponLevels.SNIPER_MINE_LEVEL_4,
    },
    Rac5WeaponKeys.SCORCHER: {
        2: Rac5WeaponLevels.SCORCHER_LEVEL_2,
        3: Rac5WeaponLevels.SCORCHER_LEVEL_3,
        4: Rac5WeaponLevels.SCORCHER_LEVEL_4,
    },
    Rac5WeaponKeys.LASER_TRACER: {
        2: Rac5WeaponLevels.LASER_TRACER_LEVEL_2,
        3: Rac5WeaponLevels.LASER_TRACER_LEVEL_3,
        4: Rac5WeaponLevels.LASER_TRACER_LEVEL_4,
    },
    Rac5WeaponKeys.SUCK_CANNON: {
        2: Rac5WeaponLevels.SUCK_CANNON_LEVEL_2,
        3: Rac5WeaponLevels.SUCK_CANNON_LEVEL_3,
        4: Rac5WeaponLevels.SUCK_CANNON_LEVEL_4,
    },
    Rac5WeaponKeys.MOOTATOR: {
        2: Rac5WeaponLevels.MOOTATOR_LEVEL_2,
        3: Rac5WeaponLevels.MOOTATOR_LEVEL_3,
        4: Rac5WeaponLevels.MOOTATOR_LEVEL_4,
    },
    Rac5WeaponKeys.RYNO: {
        2: Rac5WeaponLevels.RYNO_LEVEL_2,
        3: Rac5WeaponLevels.RYNO_LEVEL_3,
        4: Rac5WeaponLevels.RYNO_LEVEL_4,
    },
}

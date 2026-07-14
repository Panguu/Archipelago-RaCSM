"""This module provides a class with all the string constants used for Weapon Level location names."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Rac5WeaponLevels:
    """Constant strings for each Weapon Level location name — one location per
    weapon per level (1-4, matching every weapon's max level)."""

    LACERATOR_LEVEL_1 = "Lacerator: Level 1"
    LACERATOR_LEVEL_2 = "Lacerator: Level 2"
    LACERATOR_LEVEL_3 = "Lacerator: Level 3"
    LACERATOR_LEVEL_4 = "Lacerator: Level 4"

    CONCUSSION_GUN_LEVEL_1 = "Concussion Gun: Level 1"
    CONCUSSION_GUN_LEVEL_2 = "Concussion Gun: Level 2"
    CONCUSSION_GUN_LEVEL_3 = "Concussion Gun: Level 3"
    CONCUSSION_GUN_LEVEL_4 = "Concussion Gun: Level 4"

    ACID_BOMB_GLOVE_LEVEL_1 = "Acid Bomb Glove: Level 1"
    ACID_BOMB_GLOVE_LEVEL_2 = "Acid Bomb Glove: Level 2"
    ACID_BOMB_GLOVE_LEVEL_3 = "Acid Bomb Glove: Level 3"
    ACID_BOMB_GLOVE_LEVEL_4 = "Acid Bomb Glove: Level 4"

    AGENTS_OF_DOOM_LEVEL_1 = "Agents of Doom: Level 1"
    AGENTS_OF_DOOM_LEVEL_2 = "Agents of Doom: Level 2"
    AGENTS_OF_DOOM_LEVEL_3 = "Agents of Doom: Level 3"
    AGENTS_OF_DOOM_LEVEL_4 = "Agents of Doom: Level 4"

    BEE_MINE_GLOVE_LEVEL_1 = "Bee Mine Glove: Level 1"
    BEE_MINE_GLOVE_LEVEL_2 = "Bee Mine Glove: Level 2"
    BEE_MINE_GLOVE_LEVEL_3 = "Bee Mine Glove: Level 3"
    BEE_MINE_GLOVE_LEVEL_4 = "Bee Mine Glove: Level 4"

    STATIC_BARRIER_LEVEL_1 = "Static Barrier: Level 1"
    STATIC_BARRIER_LEVEL_2 = "Static Barrier: Level 2"
    STATIC_BARRIER_LEVEL_3 = "Static Barrier: Level 3"
    STATIC_BARRIER_LEVEL_4 = "Static Barrier: Level 4"

    SHOCK_ROCKET_LEVEL_1 = "Shock Rocket: Level 1"
    SHOCK_ROCKET_LEVEL_2 = "Shock Rocket: Level 2"
    SHOCK_ROCKET_LEVEL_3 = "Shock Rocket: Level 3"
    SHOCK_ROCKET_LEVEL_4 = "Shock Rocket: Level 4"

    SNIPER_MINE_LEVEL_1 = "Sniper Mine: Level 1"
    SNIPER_MINE_LEVEL_2 = "Sniper Mine: Level 2"
    SNIPER_MINE_LEVEL_3 = "Sniper Mine: Level 3"
    SNIPER_MINE_LEVEL_4 = "Sniper Mine: Level 4"

    LASER_TRACER_LEVEL_1 = "Laser Tracer: Level 1"
    LASER_TRACER_LEVEL_2 = "Laser Tracer: Level 2"
    LASER_TRACER_LEVEL_3 = "Laser Tracer: Level 3"
    LASER_TRACER_LEVEL_4 = "Laser Tracer: Level 4"

    SCORCHER_LEVEL_1 = "Scorcher: Level 1"
    SCORCHER_LEVEL_2 = "Scorcher: Level 2"
    SCORCHER_LEVEL_3 = "Scorcher: Level 3"
    SCORCHER_LEVEL_4 = "Scorcher: Level 4"

    SUCK_CANNON_LEVEL_1 = "Suck Cannon: Level 1"
    SUCK_CANNON_LEVEL_2 = "Suck Cannon: Level 2"
    SUCK_CANNON_LEVEL_3 = "Suck Cannon: Level 3"
    SUCK_CANNON_LEVEL_4 = "Suck Cannon: Level 4"

    MOOTATOR_LEVEL_1 = "Mootator: Level 1"
    MOOTATOR_LEVEL_2 = "Mootator: Level 2"
    MOOTATOR_LEVEL_3 = "Mootator: Level 3"
    MOOTATOR_LEVEL_4 = "Mootator: Level 4"

    RYNO_LEVEL_1 = "RYNO: Level 1"
    RYNO_LEVEL_2 = "RYNO: Level 2"
    RYNO_LEVEL_3 = "RYNO: Level 3"
    RYNO_LEVEL_4 = "RYNO: Level 4"

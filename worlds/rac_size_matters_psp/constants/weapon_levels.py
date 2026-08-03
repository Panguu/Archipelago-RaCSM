"""This module provides a class with all the string constants used for Weapon Level location names."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Rac5WeaponLevels:
    """Constant strings for each Weapon Level location name — one location per
    weapon per level (2-4; level 1 is synonymous with owning the weapon at
    all, so it isn't modelled as its own location)."""

    LACERATOR_LEVEL_2 = "Weapon Level: Lacerator V2"
    LACERATOR_LEVEL_3 = "Weapon Level: Lacerator V3"
    LACERATOR_LEVEL_4 = "Weapon Level: Lacerator V4"

    CONCUSSION_GUN_LEVEL_2 = "Weapon Level: Concussion Gun V2"
    CONCUSSION_GUN_LEVEL_3 = "Weapon Level: Concussion Gun V3"
    CONCUSSION_GUN_LEVEL_4 = "Weapon Level: Concussion Gun V4"

    ACID_BOMB_GLOVE_LEVEL_2 = "Weapon Level: Acid Bomb Glove V2"
    ACID_BOMB_GLOVE_LEVEL_3 = "Weapon Level: Acid Bomb Glove V3"
    ACID_BOMB_GLOVE_LEVEL_4 = "Weapon Level: Acid Bomb Glove V4"

    AGENTS_OF_DOOM_LEVEL_2 = "Weapon Level: Agents of Doom V2"
    AGENTS_OF_DOOM_LEVEL_3 = "Weapon Level: Agents of Doom V3"
    AGENTS_OF_DOOM_LEVEL_4 = "Weapon Level: Agents of Doom V4"

    BEE_MINE_GLOVE_LEVEL_2 = "Weapon Level: Bee Mine Glove V2"
    BEE_MINE_GLOVE_LEVEL_3 = "Weapon Level: Bee Mine Glove V3"
    BEE_MINE_GLOVE_LEVEL_4 = "Weapon Level: Bee Mine Glove V4"

    STATIC_BARRIER_LEVEL_2 = "Weapon Level: Static Barrier V2"
    STATIC_BARRIER_LEVEL_3 = "Weapon Level: Static Barrier V3"
    STATIC_BARRIER_LEVEL_4 = "Weapon Level: Static Barrier V4"

    SHOCK_ROCKET_LEVEL_2 = "Weapon Level: Shock Rocket V2"
    SHOCK_ROCKET_LEVEL_3 = "Weapon Level: Shock Rocket V3"
    SHOCK_ROCKET_LEVEL_4 = "Weapon Level: Shock Rocket V4"

    SNIPER_MINE_LEVEL_2 = "Weapon Level: Sniper Mine V2"
    SNIPER_MINE_LEVEL_3 = "Weapon Level: Sniper Mine V3"
    SNIPER_MINE_LEVEL_4 = "Weapon Level: Sniper Mine V4"

    LASER_TRACER_LEVEL_2 = "Weapon Level: Laser Tracer V2"
    LASER_TRACER_LEVEL_3 = "Weapon Level: Laser Tracer V3"
    LASER_TRACER_LEVEL_4 = "Weapon Level: Laser Tracer V4"

    SCORCHER_LEVEL_2 = "Weapon Level: Scorcher V2"
    SCORCHER_LEVEL_3 = "Weapon Level: Scorcher V3"
    SCORCHER_LEVEL_4 = "Weapon Level: Scorcher V4"

    SUCK_CANNON_LEVEL_2 = "Weapon Level: Suck Cannon V2"
    SUCK_CANNON_LEVEL_3 = "Weapon Level: Suck Cannon V3"
    SUCK_CANNON_LEVEL_4 = "Weapon Level: Suck Cannon V4"

    MOOTATOR_LEVEL_2 = "Weapon Level: Mootator V2"
    MOOTATOR_LEVEL_3 = "Weapon Level: Mootator V3"
    MOOTATOR_LEVEL_4 = "Weapon Level: Mootator V4"

    RYNO_LEVEL_2 = "Weapon Level: RYNO V2"
    RYNO_LEVEL_3 = "Weapon Level: RYNO V3"
    RYNO_LEVEL_4 = "Weapon Level: RYNO V4"

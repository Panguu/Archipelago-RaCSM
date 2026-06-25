from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import (
    Rac5ClankChallenges as RACSMCLANK,
    Rac5Gadgets,
    Rac5SkillPoints,
    Rac5TBolts,
    Rac5CutsceneLocations,
)

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_metalis_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    # Skill Points
    # METALIS_TERROR is commented out in core/skill_points.py — Giant Clank disabled.
    if world.options.enable_clank_challenge_skill_points:
        mw.get_location(Rac5SkillPoints.METALIS_SHUTOUT,   player).access_rule = lambda _: True
        mw.get_location(Rac5SkillPoints.METALIS_GLADIATOR, player).access_rule = lambda _: True

    # Missions
    # METALIS_ESCAPE is commented out in locations.py/missions.py — Giant Clank disabled.
    if world.options.all_missions:
        mw.get_location(Rac5CutsceneLocations.METALIS_WAR,    player).access_rule = lambda _: True

    # Titanium Bolts
    mw.get_location(Rac5TBolts.METALIS_DOOR, player).access_rule = \
        lambda state: state.has(Rac5Gadgets.POLARIZER, player) and state.has(Rac5Gadgets.HYPERSHOT, player)

    # Clank Challenges — item rewards (clank_challenges >= 1)
    if world.options.clank_challenges.value >= 1:
        mw.get_location(RACSMCLANK.METALIS_BUZZSAW, player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.METALIS_REVENGE, player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.METALIS_UBER,    player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.METALIS_NIGHT,   player).access_rule = lambda _: True

    # Clank Challenges — individual completions (clank_challenges >= 2)
    if world.options.clank_challenges.value >= 2:
        mw.get_location(RACSMCLANK.METALLIS_TEAM,        player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.METALIS_CHARGE,       player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.METALIS_BOOGALOO,     player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.METALIS_SHOWDOWN,     player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.METALIS_LEAGUE,       player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.METALIS_BRACKET,      player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.METALIS_DIVISION,     player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.METALIS_PROFESSIONAL, player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.METALIS_GAP,          player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.METALIS_TELEPORTERS,  player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.METALIS_BRAIN,        player).access_rule = lambda _: True

    # No vendor on Metalis

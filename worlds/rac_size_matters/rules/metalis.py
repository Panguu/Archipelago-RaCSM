from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import (
    Rac5ClankChallenges as RACSMCLANK,
    Rac5Gadgets,
    Rac5SkillPoints,
    Rac5TBolts,
    Rac5CutsceneLocations,
)
from rule_builder.rules import HasAll, True_

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_metalis_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    # Skill Points
    # METALIS_TERROR is commented out in core/skill_points.py — Giant Clank disabled.
    if world.options.enable_clank_challenge_skill_points:
        world.set_rule(mw.get_location(Rac5SkillPoints.METALIS_SHUTOUT, player), True_())
        world.set_rule(mw.get_location(Rac5SkillPoints.METALIS_GLADIATOR, player), True_())

    # Missions
    # METALIS_ESCAPE is commented out in locations.py/missions.py — Giant Clank disabled.
    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.METALIS_WAR, player), True_())

    # Titanium Bolts
    world.set_rule(
        mw.get_location(Rac5TBolts.METALIS_DOOR, player),
        HasAll(Rac5Gadgets.POLARIZER, Rac5Gadgets.HYPERSHOT),
    )

    # Clank Challenges — item rewards (clank_challenges >= 1)
    if world.options.clank_challenges.value >= 1:
        world.set_rule(mw.get_location(RACSMCLANK.METALIS_BUZZSAW, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.METALIS_REVENGE, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.METALIS_UBER, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.METALIS_NIGHT, player), True_())

    # Clank Challenges — individual completions (clank_challenges >= 2)
    if world.options.clank_challenges.value >= 2:
        world.set_rule(mw.get_location(RACSMCLANK.METALLIS_TEAM, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.METALIS_CHARGE, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.METALIS_BOOGALOO, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.METALIS_SHOWDOWN, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.METALIS_LEAGUE, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.METALIS_BRACKET, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.METALIS_DIVISION, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.METALIS_PROFESSIONAL, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.METALIS_GAP, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.METALIS_TELEPORTERS, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.METALIS_BRAIN, player), True_())

    # No vendor on Metalis

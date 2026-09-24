from ..constants.missions import SACMissionLocations
"""Glaciara, Ski Slopes's per-location rules -- every location belonging to this case is set here explicitly (mirrors worlds/rac_size_matters/rules' per-planet files, one world.set_rule() call per location, grouped by which options.py toggle gates that location's category -- a location only exists in the multiworld at all when its category's option is on, so calling get_location() on it unguarded would raise)."""
from typing import TYPE_CHECKING

from rule_builder.rules import True_

from ..constants.skillpoints import SACSkillPointLocations
from ..constants.special_challenges import SACSpecialChallengeLocations
from ..options import Missions

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld


def set_glaciara_ski_slopes_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld

    # Always-on
    world.set_rule(
        mw.get_location(SACSpecialChallengeLocations.GLACIARA_SKI_SLOPES_VEHICLE_VILLA_ESCAPE, player), True_(),
    )
    world.set_rule(
        mw.get_location(SACSpecialChallengeLocations.GLACIARA_SKI_SLOPES_VEHICLE_BLACK_DIAMOND, player), True_(),
    )
    world.set_rule(
        mw.get_location(SACSpecialChallengeLocations.GLACIARA_SKI_SLOPES_VEHICLE_GO_FOR_THE_GOLD, player), True_(),
    )

    # Story mission (Missions)
    if world.options.all_missions.value == Missions.option_all:
        world.set_rule(mw.get_location(SACMissionLocations.GLACIARA_SKI_SLOPES_BLACK_DIAMOND_OF_DOOM, player), True_())
        world.set_rule(mw.get_location(SACMissionLocations.GLACIARA_SKI_SLOPES_PRO_BOARDING, player), True_())
    else:
        world.set_rule(mw.get_location(SACMissionLocations.GLACIARA_SKI_SLOPES_COMPLETE, player), True_())

    # Skill point (SkillPoints)
    if world.options.skill_points:
        world.set_rule(mw.get_location(SACSkillPointLocations.GLACIARA_SKI_SLOPES_BLACK_DIAMOND, player), True_())
        world.set_rule(mw.get_location(SACSkillPointLocations.GLACIARA_SKI_SLOPES_SMOOTH_MOVES, player), True_())
        world.set_rule(mw.get_location(SACSkillPointLocations.GLACIARA_SKI_SLOPES_RINGLEADER, player), True_())

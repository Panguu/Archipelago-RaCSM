from ..constants.cutscenes import SACCutsceneLocations
"""Venantonio Canals's per-location rules -- every location belonging to this case is set here explicitly (mirrors worlds/rac_size_matters/rules' per-planet files, one world.set_rule() call per location, grouped by which options.py toggle gates that location's category -- a location only exists in the multiworld at all when its category's option is on, so calling get_location() on it unguarded would raise)."""
from typing import TYPE_CHECKING

from rule_builder.rules import True_

from ..constants.missions import SACMissionLocations
from ..constants.skillpoints import SACSkillPointLocations
from ..constants.special_challenges import SACSpecialChallengeLocations
from ..options import Missions

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld


def set_venantonio_canals_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld

    # Always-on
    world.set_rule(
        mw.get_location(SACSpecialChallengeLocations.VENANTONIO_CANALS_VEHICLE_GREAT_ESCAPE, player), True_(),
    )
    world.set_rule(
        mw.get_location(SACSpecialChallengeLocations.VENANTONIO_CANALS_VEHICLE_SPEEDBOATING, player), True_(),
    )
    world.set_rule(
        mw.get_location(SACSpecialChallengeLocations.VENANTONIO_CANALS_VEHICLE_THREADING_THE_NEEDLE, player), True_(),
    )

    # Story mission (Missions)
    if world.options.all_missions.value == Missions.option_all:
        world.set_rule(mw.get_location(SACMissionLocations.VENANTONIO_CANALS_DANGER_OFF_STARBOARD, player), True_())
        world.set_rule(mw.get_location(SACMissionLocations.VENANTONIO_CANALS_POWER_JET_BOATING, player), True_())
    else:
        world.set_rule(mw.get_location(SACMissionLocations.VENANTONIO_CANALS_COMPLETE, player), True_())

    # Cutscene (AllCutscenes)
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(SACCutsceneLocations.VENANTONIO_CANALS_COMPLETE_CUTSCENE, player), True_())

    # Skill point (SkillPoints)
    if world.options.skill_points:
        world.set_rule(mw.get_location(SACSkillPointLocations.VENANTONIO_CANALS_EVASIVE_MANEUVERS, player), True_())
        world.set_rule(mw.get_location(SACSkillPointLocations.VENANTONIO_CANALS_DEEP_SIX, player), True_())
        world.set_rule(mw.get_location(SACSkillPointLocations.VENANTONIO_CANALS_WAKE_OF_DESTRUCTION, player), True_())
        world.set_rule(mw.get_location(SACSkillPointLocations.VENANTONIO_CANALS_RINGMASTER, player), True_())

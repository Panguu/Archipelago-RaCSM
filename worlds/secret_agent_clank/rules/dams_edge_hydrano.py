from ..constants.cutscenes import SACCutsceneLocations
"""Dam's Edge, Hydrano's per-location rules -- every location belonging to this case is set here explicitly (mirrors worlds/rac_size_matters/rules' per-planet files, one world.set_rule() call per location, grouped by which options.py toggle gates that location's category -- a location only exists in the multiworld at all when its category's option is on, so calling get_location() on it unguarded would raise)."""
from typing import TYPE_CHECKING

from rule_builder.rules import True_

from ..constants.missions import SACMissionLocations
from ..constants.skillpoints import SACSkillPointLocations
from ..constants.special_challenges import SACSpecialChallengeLocations
from ..options import Missions

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld


def set_dams_edge_hydrano_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld

    # Always-on
    world.set_rule(
        mw.get_location(SACSpecialChallengeLocations.DAMS_EDGE_HYDRANO_VEHICLE_CHASING_A_LEAD, player), True_(),
    )
    world.set_rule(mw.get_location(SACSpecialChallengeLocations.DAMS_EDGE_HYDRANO_VEHICLE_RUSH_HOUR, player), True_())
    world.set_rule(
        mw.get_location(SACSpecialChallengeLocations.DAMS_EDGE_HYDRANO_VEHICLE_DRIVING_TEST, player), True_(),
    )

    # Story mission (Missions)
    if world.options.all_missions.value == Missions.option_all:
        world.set_rule(mw.get_location(SACMissionLocations.DAMS_EDGE_HYDRANO_SHIP_S_SIGNAL, player), True_())
        world.set_rule(mw.get_location(SACMissionLocations.DAMS_EDGE_HYDRANO_FOLLOW_THAT_CAR, player), True_())
        world.set_rule(mw.get_location(SACMissionLocations.DAMS_EDGE_HYDRANO_THE_DRIFT_KING, player), True_())
    else:
        world.set_rule(mw.get_location(SACMissionLocations.DAMS_EDGE_HYDRANO_COMPLETE, player), True_())

    # Cutscene (AllCutscenes)
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(SACCutsceneLocations.DAMS_EDGE_HYDRANO_ENTER_CUTSCENE, player), True_())
        world.set_rule(mw.get_location(SACCutsceneLocations.DAMS_EDGE_HYDRANO_COMPLETE_CUTSCENE, player), True_())

    # Skill point (SkillPoints)
    if world.options.skill_points:
        world.set_rule(mw.get_location(SACSkillPointLocations.DAMS_EDGE_HYDRANO_YEEE_HAAAAAW, player), True_())
        world.set_rule(mw.get_location(SACSkillPointLocations.DAMS_EDGE_HYDRANO_OFFENSIVE_DRIVER, player), True_())
        world.set_rule(mw.get_location(SACSkillPointLocations.DAMS_EDGE_HYDRANO_SLIPPERY_SLOPE, player), True_())
        world.set_rule(mw.get_location(SACSkillPointLocations.DAMS_EDGE_HYDRANO_RING_AROUND_THE_ROSIE, player), True_())

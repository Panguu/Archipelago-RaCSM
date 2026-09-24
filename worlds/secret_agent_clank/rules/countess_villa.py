from ..constants.cutscenes import SACCutsceneLocations
"""Countess's Villa's per-location rules -- every location belonging to this case is set here explicitly (mirrors worlds/rac_size_matters/rules' per-planet files, one world.set_rule() call per location, grouped by which options.py toggle gates that location's category -- a location only exists in the multiworld at all when its category's option is on, so calling get_location() on it unguarded would raise)."""
from typing import TYPE_CHECKING

from rule_builder.rules import True_

from ..constants.missions import SACMissionLocations
from ..constants.skillpoints import SACSkillPointLocations
from ..options import Missions

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld


def set_countess_villa_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld

    # Story mission (Missions)
    if world.options.all_missions.value == Missions.option_all:
        world.set_rule(mw.get_location(SACMissionLocations.COUNTESS_VILLA_TANGO_OF_100_SORROWS, player), True_())
    else:
        world.set_rule(mw.get_location(SACMissionLocations.COUNTESS_VILLA_COMPLETE, player), True_())

    # Cutscene (AllCutscenes)
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(SACCutsceneLocations.COUNTESS_VILLA_ENTER_THE_MANSION, player), True_())
        world.set_rule(mw.get_location(SACCutsceneLocations.COUNTESS_VILLA_COMPLETE_DANCE_CUTSCENE, player), True_())

    # Skill point (SkillPoints)
    if world.options.skill_points:
        world.set_rule(mw.get_location(SACSkillPointLocations.COUNTESS_VILLA_PERFECT_TANGO, player), True_())

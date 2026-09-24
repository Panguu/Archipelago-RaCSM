from ..constants.cutscenes import SACCutsceneLocations
"""A Fiction Full Of Dollars's per-location rules -- every location belonging to this case is set here explicitly (mirrors worlds/rac_size_matters/rules' per-planet files, one world.set_rule() call per location, grouped by which options.py toggle gates that location's category -- a location only exists in the multiworld at all when its category's option is on, so calling get_location() on it unguarded would raise)."""
from typing import TYPE_CHECKING

from rule_builder.rules import True_

from ..constants.missions import SACMissionLocations
from ..constants.skillpoints import SACSkillPointLocations
from ..options import Missions

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld


def set_a_fiction_full_of_dollars_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld

    # Story mission (Missions)
    if world.options.all_missions.value == Missions.option_all:
        world.set_rule(
            mw.get_location(SACMissionLocations.A_FICTION_FULL_OF_DOLLARS_QWARKOGRAPHY_CH_5, player), True_(),
        )
    else:
        world.set_rule(mw.get_location(SACMissionLocations.A_FICTION_FULL_OF_DOLLARS_COMPLETE, player), True_())

    # Cutscene (AllCutscenes)
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(SACCutsceneLocations.A_FICTION_FULL_OF_DOLLARS_ENTER_CUTSCENE, player), True_())
        world.set_rule(
            mw.get_location(SACCutsceneLocations.A_FICTION_FULL_OF_DOLLARS_COMPLETE_CUTSCENE, player), True_(),
        )

    # Skill point (SkillPoints)
    if world.options.skill_points:
        world.set_rule(
            mw.get_location(SACSkillPointLocations.A_FICTION_FULL_OF_DOLLARS_CLEANS_POOLS_TOO, player), True_(),
        )
        world.set_rule(
            mw.get_location(SACSkillPointLocations.A_FICTION_FULL_OF_DOLLARS_PERFECT_MIRROR, player), True_(),
        )

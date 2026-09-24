"""Rooftop Deathtrap's per-location rules -- every location belonging to this case is set here explicitly (mirrors worlds/rac_size_matters/rules' per-planet files, one world.set_rule() call per location, grouped by which options.py toggle gates that location's category -- a location only exists in the multiworld at all when its category's option is on, so calling get_location() on it unguarded would raise)."""
from typing import TYPE_CHECKING

from rule_builder.rules import True_

from ..constants.clank_gadgets import SACClankGadgets, SACClankWeapons
from ..constants.cutscenes import SACCutsceneLocations
from ..constants.gadgetbot_challenges import SACGadgetbotChallengeLocations
from ..constants.missions import SACMissionLocations
from ..constants.skillpoints import SACSkillPointLocations
from ..constants.weapons import SACRatchetWeapons
from ..options import Missions

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld


def set_rooftop_deathtrap_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld

    # Always-on
    world.set_rule(mw.get_location(SACRatchetWeapons.MINELAUNCHER, player), True_())
    world.set_rule(mw.get_location(SACClankWeapons.CUFFLINK, player), True_())
    world.set_rule(mw.get_location(SACClankGadgets.OMNIKEY, player), True_())
    world.set_rule(mw.get_location(SACGadgetbotChallengeLocations.ROOFTOP_DEATHTRAP_RESCUE_CLANK, player), True_())
    world.set_rule(mw.get_location(SACGadgetbotChallengeLocations.ROOFTOP_DEATHTRAP_WORKING_DOWN, player), True_())
    world.set_rule(mw.get_location(SACGadgetbotChallengeLocations.ROOFTOP_DEATHTRAP_GREAT_DIVIDE, player), True_())

    # Story mission (Missions)
    if world.options.all_missions.value == Missions.option_all:
        world.set_rule(mw.get_location(SACMissionLocations.ROOFTOP_DEATHTRAP_GET_A_CLUE, player), True_())
        world.set_rule(mw.get_location(SACMissionLocations.ROOFTOP_DEATHTRAP_FREE_AGENT_CLANK, player), True_())
        world.set_rule(mw.get_location(SACMissionLocations.ROOFTOP_DEATHTRAP_THE_HALLS_OF_ASYANICA, player), True_())
    else:
        world.set_rule(mw.get_location(SACMissionLocations.ROOFTOP_DEATHTRAP_COMPLETE, player), True_())

    # Cutscene (AllCutscenes)
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(SACCutsceneLocations.ROOFTOP_DEATHTRAP_ENTER_CUTSCENE, player), True_())
        world.set_rule(mw.get_location(SACCutsceneLocations.ROOFTOP_DEATHTRAP_RESCURE_CLANK_CUTSCENE, player), True_())

    # Skill point (SkillPoints)
    if world.options.skill_points:
        world.set_rule(mw.get_location(SACSkillPointLocations.ROOFTOP_DEATHTRAP_SPEED_DEMON, player), True_())
        world.set_rule(mw.get_location(SACSkillPointLocations.ROOFTOP_DEATHTRAP_PERFECT_CHROME_FINISH, player), True_())

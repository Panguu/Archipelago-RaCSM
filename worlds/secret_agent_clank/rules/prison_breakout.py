from ..constants.cutscenes import SACCutsceneLocations
"""Prison Breakout!'s per-location rules -- every location belonging to this case is set here explicitly (mirrors worlds/rac_size_matters/rules' per-planet files, one world.set_rule() call per location, grouped by which options.py toggle gates that location's category -- a location only exists in the multiworld at all when its category's option is on, so calling get_location() on it unguarded would raise)."""
from typing import TYPE_CHECKING

from rule_builder.rules import True_

from ..constants.missions import SACMissionLocations
from ..constants.ratchet_challenges import SACRatchetChallengeLocations
from ..constants.skillpoints import SACSkillPointLocations
from ..constants.titanium_bolts import SACTitaniumBoltLocations
from ..options import Missions

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld


def set_prison_breakout_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld

    # Always-on
    world.set_rule(mw.get_location(SACRatchetChallengeLocations.PRISON_BREAKOUT_CATCH_AS_CATCH_CAN, player), True_())
    world.set_rule(mw.get_location(SACRatchetChallengeLocations.PRISON_BREAKOUT_AMOEBOID_ON_A_POLE, player), True_())
    world.set_rule(mw.get_location(SACRatchetChallengeLocations.PRISON_BREAKOUT_IRON_MAN, player), True_())
    world.set_rule(mw.get_location(SACRatchetChallengeLocations.PRISON_BREAKOUT_TRIPLE_THREAT, player), True_())
    world.set_rule(
        mw.get_location(SACRatchetChallengeLocations.PRISON_BREAKOUT_MEGA_CHALLENGE_BATTLE_ROYAL, player), True_(),
    )
    world.set_rule(mw.get_location(SACTitaniumBoltLocations.PRISON_BREAKOUT_1, player), True_())

    # Story mission (Missions)
    if world.options.all_missions.value == Missions.option_all:
        world.set_rule(mw.get_location(SACMissionLocations.PRISON_BREAKOUT_THE_GREAT_ESCAPE, player), True_())
        world.set_rule(mw.get_location(SACMissionLocations.PRISON_BREAKOUT_AND_NOW_JUSTICE_FOR_ALL, player), True_())
    else:
        world.set_rule(mw.get_location(SACMissionLocations.PRISON_BREAKOUT_COMPLETE, player), True_())

    # Cutscene (AllCutscenes)
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(SACCutsceneLocations.PRISON_BREAKOUT_ENTER_CUTSCENE, player), True_())

    # Skill point (SkillPoints)
    if world.options.skill_points:
        world.set_rule(mw.get_location(SACSkillPointLocations.PRISON_BREAKOUT_WHIP_IT_GOOD, player), True_())
        world.set_rule(mw.get_location(SACSkillPointLocations.PRISON_BREAKOUT_HANGING_JUDGE, player), True_())

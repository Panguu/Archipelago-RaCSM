from ..constants.cutscenes import SACCutsceneLocations
"""The Exercise Yard's per-location rules -- every location belonging to this case is set here explicitly (mirrors worlds/rac_size_matters/rules' per-planet files, one world.set_rule() call per location, grouped by which options.py toggle gates that location's category -- a location only exists in the multiworld at all when its category's option is on, so calling get_location() on it unguarded would raise)."""
from typing import TYPE_CHECKING

from rule_builder.rules import True_

from ..constants.missions import SACMissionLocations
from ..constants.ratchet_challenges import SACRatchetChallengeLocations
from ..constants.skillpoints import SACSkillPointLocations
from ..constants.titanium_bolts import SACTitaniumBoltLocations
from ..options import Missions

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld


def set_the_exercise_yard_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld

    # Always-on
    world.set_rule(
        mw.get_location(SACRatchetChallengeLocations.THE_EXERCISE_YARD_LAST_ONE_PICKED_FOR_DODGEBALL, player), True_(),
    )
    world.set_rule(mw.get_location(SACRatchetChallengeLocations.THE_EXERCISE_YARD_STEEL_IS_STEEL, player), True_())
    world.set_rule(
        mw.get_location(SACRatchetChallengeLocations.THE_EXERCISE_YARD_PUMPING_IRON_MOLTEN_IRON, player), True_(),
    )
    world.set_rule(mw.get_location(SACRatchetChallengeLocations.THE_EXERCISE_YARD_GREAT_BALLS_OF_FIRE, player), True_())
    world.set_rule(
        mw.get_location(SACRatchetChallengeLocations.THE_EXERCISE_YARD_MEGA_CHALLENGE_PRISON_YARD, player), True_(),
    )
    world.set_rule(mw.get_location(SACTitaniumBoltLocations.THE_EXERCISE_YARD_1, player), True_())

    # Story mission (Missions)
    if world.options.all_missions.value == Missions.option_all:
        world.set_rule(mw.get_location(SACMissionLocations.THE_EXERCISE_YARD_AND_THE_PASSWORD_IS, player), True_())
        world.set_rule(mw.get_location(SACMissionLocations.THE_EXERCISE_YARD_FIGHT_FOR_SLIM, player), True_())
    else:
        world.set_rule(mw.get_location(SACMissionLocations.THE_EXERCISE_YARD_COMPLETE, player), True_())

    # Cutscene (AllCutscenes)
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(SACCutsceneLocations.THE_EXERCISE_YARD_COMPLETE_CUTSCENE, player), True_())

    # Skill point (SkillPoints)
    if world.options.skill_points:
        world.set_rule(mw.get_location(SACSkillPointLocations.THE_EXERCISE_YARD_INDIAN_BURN, player), True_())
        world.set_rule(mw.get_location(SACSkillPointLocations.THE_EXERCISE_YARD_LAW_CANT_TOUCH_ME, player), True_())

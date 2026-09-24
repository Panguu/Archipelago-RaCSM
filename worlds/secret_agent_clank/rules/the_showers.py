from ..constants.cutscenes import SACCutsceneLocations
"""The Showers's per-location rules -- every location belonging to this case is set here explicitly (mirrors worlds/rac_size_matters/rules' per-planet files, one world.set_rule() call per location, grouped by which options.py toggle gates that location's category -- a location only exists in the multiworld at all when its category's option is on, so calling get_location() on it unguarded would raise)."""
from typing import TYPE_CHECKING

from rule_builder.rules import True_

from ..constants.missions import SACMissionLocations
from ..constants.ratchet_challenges import SACRatchetChallengeLocations
from ..constants.skillpoints import SACSkillPointLocations
from ..constants.titanium_bolts import SACTitaniumBoltLocations
from ..options import Missions

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld


def set_the_showers_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld

    # Always-on
    world.set_rule(
        mw.get_location(SACRatchetChallengeLocations.THE_SHOWERS_NO_GOOD_DEED_GOES_UNPUNISHED, player), True_(),
    )
    world.set_rule(mw.get_location(SACRatchetChallengeLocations.THE_SHOWERS_COVER_YOUR_SHAME, player), True_())
    world.set_rule(mw.get_location(SACRatchetChallengeLocations.THE_SHOWERS_DIDNT_NEED_TO_SEE_THAT, player), True_())
    world.set_rule(mw.get_location(SACRatchetChallengeLocations.THE_SHOWERS_ITS_A_DRY_HEAT, player), True_())
    world.set_rule(mw.get_location(SACRatchetChallengeLocations.THE_SHOWERS_MEGA_CHALLENGE_SHOWER, player), True_())
    world.set_rule(mw.get_location(SACTitaniumBoltLocations.THE_SHOWERS_1, player), True_())

    # Story mission (Missions)
    if world.options.all_missions.value == Missions.option_all:
        world.set_rule(mw.get_location(SACMissionLocations.THE_SHOWERS_PLUMBING_TROUBLES, player), True_())
        world.set_rule(mw.get_location(SACMissionLocations.THE_SHOWERS_RUB_A_DUB_DEATH, player), True_())
    else:
        world.set_rule(mw.get_location(SACMissionLocations.THE_SHOWERS_COMPLETE, player), True_())

    # Cutscene (AllCutscenes)
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(SACCutsceneLocations.THE_SHOWERS_ENTER_CUTSCENE, player), True_())

    # Skill point (SkillPoints)
    if world.options.skill_points:
        world.set_rule(mw.get_location(SACSkillPointLocations.THE_SHOWERS_RUBA_DUB_CLUB, player), True_())
        world.set_rule(mw.get_location(SACSkillPointLocations.THE_SHOWERS_MODESTY, player), True_())

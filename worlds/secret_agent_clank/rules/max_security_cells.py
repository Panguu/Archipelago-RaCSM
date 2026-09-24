"""Max-Security Cells's per-location rules -- every location belonging to this case is set here explicitly (mirrors worlds/rac_size_matters/rules' per-planet files, one world.set_rule() call per location, grouped by which options.py toggle gates that location's category -- a location only exists in the multiworld at all when its category's option is on, so calling get_location() on it unguarded would raise)."""
from typing import TYPE_CHECKING

from rule_builder.rules import True_

from ..constants.cutscenes import SACCutsceneLocations
from ..constants.missions import SACMissionLocations
from ..constants.ratchet_challenges import SACRatchetChallengeLocations
from ..constants.skillpoints import SACSkillPointLocations
from ..constants.titanium_bolts import SACTitaniumBoltLocations
from ..constants.weapons import SACRatchetWeapons
from ..options import Missions

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld


def set_max_security_cells_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld

    # Always-on
    world.set_rule(mw.get_location(SACRatchetWeapons.SHARDGUN, player), True_())
    world.set_rule(mw.get_location(SACRatchetWeapons.WALLOPER, player), True_())


    world.set_rule(mw.get_location(SACRatchetChallengeLocations.MAX_SECURITY_CELLS_KARMIC_BREAKDOWN, player), True_())
    world.set_rule(mw.get_location(SACRatchetChallengeLocations.MAX_SECURITY_CELLS_NO_SHELTER, player), True_())
    world.set_rule(mw.get_location(SACRatchetChallengeLocations.MAX_SECURITY_CELLS_PAST_DUE, player), True_())
    world.set_rule(mw.get_location(SACRatchetChallengeLocations.MAX_SECURITY_CELLS_SPEAK_SOFTLY_AND, player), True_())
    world.set_rule(
        mw.get_location(SACRatchetChallengeLocations.MAX_SECURITY_CELLS_MEGA_CHALLENGE_CELLBLOCK, player), True_(),
    )
    world.set_rule(mw.get_location(SACTitaniumBoltLocations.MAX_SECURITY_CELLS_1, player), True_())

    # Story mission (Missions)
    if world.options.all_missions.value == Missions.option_all:
        world.set_rule(mw.get_location(SACMissionLocations.MAX_SECURITY_CELLS_LIFE_IN_PRISON, player), True_())
        world.set_rule(
            mw.get_location(SACMissionLocations.MAX_SECURITY_CELLS_CONSECUTIVE_LIFE_SENTENCES, player), True_(),
        )
    else:
        world.set_rule(mw.get_location(SACMissionLocations.MAX_SECURITY_CELLS_COMPLETE, player), True_())

    # Cutscene (AllCutscenes)
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(SACCutsceneLocations.MAX_SECURITY_CELLS_ENTER_CUTSCENE, player), True_())

    # Skill point (SkillPoints)
    if world.options.skill_points:
        world.set_rule(mw.get_location(SACSkillPointLocations.MAX_SECURITY_CELLS_STAINLESS_STEEL, player), True_())
        world.set_rule(mw.get_location(SACSkillPointLocations.MAX_SECURITY_CELLS_PLAYING_WITH_FIRE, player), True_())

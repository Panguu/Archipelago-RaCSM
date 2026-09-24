"""Azcotal Alley's per-location rules -- every location belonging to this case is set here explicitly (mirrors worlds/rac_size_matters/rules' per-planet files, one world.set_rule() call per location, grouped by which options.py toggle gates that location's category -- a location only exists in the multiworld at all when its category's option is on, so calling get_location() on it unguarded would raise)."""
from typing import TYPE_CHECKING

from rule_builder.rules import True_

from ..constants.alien_codes import SACAlienCodeLocations
from ..constants.clank_gadgets import SACClankGadgets, SACClankWeapons
from ..constants.cutscenes import SACCutsceneLocations
from ..constants.missions import SACMissionLocations
from ..constants.skillpoints import SACSkillPointLocations
from ..constants.titanium_bolts import SACTitaniumBoltLocations
from ..constants.weapons import SACRatchetWeapons
from ..options import Missions
from .rule_helpers import Has

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld


def set_azcotal_alley_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld

    # Always-on
    world.set_rule(mw.get_location(SACClankWeapons.TANGLEVINE, player), True_())
    world.set_rule(mw.get_location(SACClankGadgets.CLANKPDA, player), True_())
    world.set_rule(mw.get_location(SACRatchetWeapons.BEEMINEGLOVE, player), True_())
    world.set_rule(mw.get_location(SACTitaniumBoltLocations.AZCOTAL_ALLEY_1, player), True_())
    world.set_rule(mw.get_location(SACTitaniumBoltLocations.AZCOTAL_ALLEY_2, player), True_())
    world.set_rule(mw.get_location(SACTitaniumBoltLocations.AZCOTAL_ALLEY_3, player), True_())

    # Story mission (Missions)
    if world.options.all_missions.value == Missions.option_all:
        world.set_rule(mw.get_location(SACMissionLocations.AZCOTAL_ALLEY_THE_KINGPIN, player), True_())
        world.set_rule(mw.get_location(SACMissionLocations.AZCOTAL_ALLEY_ALL_THE_KINGPIN_S_MEN, player), True_())
    else:
        world.set_rule(mw.get_location(SACMissionLocations.AZCOTAL_ALLEY_COMPLETE, player), True_())

    # Cutscene (AllCutscenes)
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(SACCutsceneLocations.AZCOTAL_ALLEY_ENTER_CUTSCENE, player), True_())
        world.set_rule(mw.get_location(SACCutsceneLocations.AZCOTAL_ALLEY_MEET_JACK_CUTSCENE, player), True_())

    # Skill point (SkillPoints)
    if world.options.skill_points:
        world.set_rule(mw.get_location(SACSkillPointLocations.AZCOTAL_ALLEY_MASTER_OF_DISGUISE, player), True_())
        world.set_rule(mw.get_location(SACSkillPointLocations.AZCOTAL_ALLEY_TRASH_TALK, player), True_())
        world.set_rule(mw.get_location(SACSkillPointLocations.AZCOTAL_ALLEY_DEADLY_HANDS, player), True_())

    # Alien code (AllAlienCodes) -- also needs Therm-Optic Shades
    if world.options.all_alien_codes:
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.AZCOTAL_ALLEY_JONS_SECRET, player), Has(SACClankGadgets.THERM_OPTIC_SHADES),
        )
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.AZCOTAL_ALLEY_THE_3_JASONS_SECRET, player),
            Has(SACClankGadgets.THERM_OPTIC_SHADES),
        )
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.AZCOTAL_ALLEY_TRAVIS_SECRET, player), Has(SACClankGadgets.THERM_OPTIC_SHADES),
        )

"""Venantonio Labs's per-location rules -- every location belonging to this case is set here explicitly (mirrors worlds/rac_size_matters/rules' per-planet files, one world.set_rule() call per location, grouped by which options.py toggle gates that location's category -- a location only exists in the multiworld at all when its category's option is on, so calling get_location() on it unguarded would raise)."""
from typing import TYPE_CHECKING

from rule_builder.rules import HasAll, True_

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


def set_venantonio_labs_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld
    _base = HasAll(SACClankWeapons.CUFFLINK, SACClankGadgets.OMNIKEY)
    _briefcase_path = HasAll(SACClankWeapons.FLAMETHROWERPEN, SACClankWeapons.CUFFLINK)
    _finish = _briefcase_path & Has(SACClankGadgets.OMNIKEY)
    # Always-on
    world.set_rule(mw.get_location(SACRatchetWeapons.PLASMAWHIP, player), True_())
    world.set_rule(mw.get_location(SACClankWeapons.FLAMETHROWERPEN, player), _base)
    world.set_rule(mw.get_location(SACClankWeapons.LIGHTNINGUMBRELLA, player), True_())
    world.set_rule(mw.get_location(SACRatchetWeapons.KICKBLAST, player), True_())
    world.set_rule(mw.get_location(SACTitaniumBoltLocations.VENANTONIO_LABS_1, player), _base)
    world.set_rule(mw.get_location(SACTitaniumBoltLocations.VENANTONIO_LABS_2, player), _briefcase_path)

    # Story mission (Missions)
    if world.options.all_missions.value == Missions.option_all:
        world.set_rule(mw.get_location(SACMissionLocations.VENANTONIO_LABS_CRASHING_THE_PARTY, player), _base)
        world.set_rule(mw.get_location(SACMissionLocations.VENANTONIO_LABS_OUT_OF_THE_FRYING_PAN, player), _finish)
    else:
        world.set_rule(mw.get_location(SACMissionLocations.VENANTONIO_LABS_COMPLETE, player), _finish)

    # Cutscene (AllCutscenes)
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(SACCutsceneLocations.VENANTONIO_LABS_ENTER_CUTSCENE, player), True_())
        world.set_rule(mw.get_location(SACCutsceneLocations.VENANTONIO_LABS_OPEN_GREEN_DOOR_CUTSCENE, player), True_())
        world.set_rule(mw.get_location(SACCutsceneLocations.VENANTONIO_LABS_COMPLETE_CUTSCENE, player), _finish)

    # Skill point (SkillPoints)
    if world.options.skill_points:
        world.set_rule(mw.get_location(SACSkillPointLocations.VENANTONIO_LABS_ALL_SLIME_MUST_BURN, player), _base & Has(SACClankWeapons.FLAMETHROWERPEN))
        world.set_rule(mw.get_location(SACSkillPointLocations.VENANTONIO_LABS_RAMMING_SPEED, player), _briefcase_path)

    # Alien code (AllAlienCodes) -- also needs Therm-Optic Shades
    if world.options.all_alien_codes:
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.VENANTONIO_LABS_GERARDS_SECRET, player),
            Has(SACClankGadgets.THERM_OPTIC_SHADES),
        )
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.VENANTONIO_LABS_ALEXS_SECRET, player),
            _briefcase_path & Has(SACClankGadgets.THERM_OPTIC_SHADES),
        )
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.VENANTONIO_LABS_HAROONS_SECRET, player),
            _briefcase_path & Has(SACClankGadgets.THERM_OPTIC_SHADES),
        )

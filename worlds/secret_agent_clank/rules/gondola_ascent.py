"""Gondola Ascent's per-location rules -- every location belonging to this case is set here explicitly (mirrors worlds/rac_size_matters/rules' per-planet files, one world.set_rule() call per location, grouped by which options.py toggle gates that location's category -- a location only exists in the multiworld at all when its category's option is on, so calling get_location() on it unguarded would raise)."""
from typing import TYPE_CHECKING

from rule_builder.rules import Has, HasAll

from ..constants.alien_codes import SACAlienCodeLocations
from ..constants.clank_gadgets import SACClankGadgets, SACClankWeapons
from ..constants.cutscenes import SACCutsceneLocations
from ..constants.missions import SACMissionLocations
from ..constants.skillpoints import SACSkillPointLocations
from ..constants.titanium_bolts import SACTitaniumBoltLocations
from ..options import Missions

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld


def set_gondola_ascent_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld
    _base = HasAll(SACClankGadgets.JETBOOTS, SACClankWeapons.TANGLEVINE)
    _omnikey = Has(SACClankGadgets.OMNIKEY) & _base
    world.set_rule(mw.get_location(SACTitaniumBoltLocations.GONDOLA_ASCENT_1, player), _base)

    if world.options.all_missions.value == Missions.option_all:
        world.set_rule(mw.get_location(SACMissionLocations.GONDOLA_ASCENT_GET_A_LIFT, player), _base)
    else:
        world.set_rule(mw.get_location(SACMissionLocations.GONDOLA_ASCENT_COMPLETE, player), _base)

    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(SACCutsceneLocations.GONDOLA_ASCENT_FINISH_GONDOLA_CUTSCENE, player), _omnikey)

    if world.options.skill_points:
        world.set_rule(mw.get_location(SACSkillPointLocations.GONDOLA_ASCENT_STEEL_RAIN, player), _base & Has(SACClankWeapons.HOLOKNUCKLES))

    if world.options.all_alien_codes:
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.GONDOLA_ASCENT_LEVITICUS_SECRET, player),
            _base & Has(SACClankGadgets.THERM_OPTIC_SHADES),
        )
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.GONDOLA_ASCENT_CARLS_SECRET, player), _base & Has(SACClankGadgets.THERM_OPTIC_SHADES),
        )
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.GONDOLA_ASCENT_JESS_SECRET, player), _base & Has(SACClankGadgets.THERM_OPTIC_SHADES),
        )

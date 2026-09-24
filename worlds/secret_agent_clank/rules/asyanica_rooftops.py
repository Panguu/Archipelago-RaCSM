"""Asyanica Rooftops's per-location rules -- every location belonging to this case is set here explicitly (mirrors worlds/rac_size_matters/rules' per-planet files, one world.set_rule() call per location, grouped by which options.py toggle gates that location's category -- a location only exists in the multiworld at all when its category's option is on, so calling get_location() on it unguarded would raise)."""
from typing import TYPE_CHECKING
from ..constants.keycards import SACKeycardLocations

from rule_builder.rules import HasAll, Has

from ..constants.alien_codes import SACAlienCodeLocations
from ..constants.clank_gadgets import SACClankGadgets, SACClankWeapons
from ..constants.missions import SACMissionLocations
from ..constants.skillpoints import SACSkillPointLocations
from ..constants.titanium_bolts import SACTitaniumBoltLocations
from ..options import Missions

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld


def set_asyanica_rooftops_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld

    _base_rule = HasAll(SACClankWeapons.THROWTIE, SACClankGadgets.JETBOOTS)
    _omnikey = _base_rule & Has(SACClankGadgets.OMNIKEY)
    # Always-on
    world.set_rule(mw.get_location(SACTitaniumBoltLocations.ASYANICA_ROOFTOPS_1, player), _base_rule)

    # Story mission (Missions)
    if world.options.all_missions.value == Missions.option_all:
        world.set_rule(mw.get_location(SACMissionLocations.ASYANICA_ROOFTOPS_NUMBER_WOO_WORKS_FOR, player), _omnikey)
    else:
        world.set_rule(mw.get_location(SACMissionLocations.ASYANICA_ROOFTOPS_COMPLETE, player), _base_rule)

    if world.options.all_keycards:
        world.set_rule(mw.get_location(SACKeycardLocations.RED_KEYCARD, player), _omnikey)
    # Skill point (SkillPoints)
    if world.options.skill_points:
        world.set_rule(mw.get_location(SACSkillPointLocations.ASYANICA_ROOFTOPS_ROBOT_FINDS_NINJA, player), _omnikey)
        world.set_rule(mw.get_location(SACSkillPointLocations.ASYANICA_ROOFTOPS_BLACK_TIE_AFFAIR, player), _omnikey)
        world.set_rule(mw.get_location(SACSkillPointLocations.ASYANICA_ROOFTOPS_LIKE_THE_WIND, player), _omnikey)

    # Alien code (AllAlienCodes) -- also needs Therm-Optic Shades
    if world.options.all_alien_codes:
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.ASYANICA_ROOFTOPS_JHAIROS_SECRET, player),
            Has(SACClankGadgets.THERM_OPTIC_SHADES) & _omnikey,
        )
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.ASYANICA_ROOFTOPS_GILBERTS_SECRET, player),
            Has(SACClankGadgets.THERM_OPTIC_SHADES) & _omnikey,
        )
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.ASYANICA_ROOFTOPS_RICARDOS_SECRET, player),
            Has(SACClankGadgets.THERM_OPTIC_SHADES) & _omnikey,
        )

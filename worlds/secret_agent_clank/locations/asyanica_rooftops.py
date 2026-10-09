"""Asyanica Rooftops: the case region and every location in it, with its access rule."""
from rule_builder.rules import Has, HasAll

from ..constants import (
    SACAlienCodeLocations,
    SACCases,
    SACClankGadgets,
    SACClankWeapons,
    SACKeycardLocations,
    SACMissionLocations,
    SACPickups,
    SACSkillPointLocations,
    SACTitaniumBoltLocations,
)
from .model import CaseRegion, SACLocation, SACLocationType

_BASE_RULE = HasAll(SACClankWeapons.THROWTIE, SACClankGadgets.JETBOOTS)
_OMNIKEY = _BASE_RULE & Has(SACClankGadgets.OMNIKEY)
COMPLETE_RULE = _OMNIKEY
"""Items to complete the case, also used by its stealth takedown checks."""

REGION = CaseRegion(SACCases.ASYANICA_ROOFTOPS, (
    SACLocation(SACPickups.ASYANICA_ROOFTOPS_MINE_LAUNCHER, SACLocationType.RATCHET_WEAPON, _OMNIKEY),
    SACLocation(SACPickups.ASYANICA_ROOFTOPS_CUFFLINK_BOMB, SACLocationType.CLANK_WEAPON, _OMNIKEY),
    SACLocation(SACPickups.ASYANICA_ROOFTOPS_OMNI_KEY, SACLocationType.CLANK_GADGET, _BASE_RULE),
    SACLocation(SACTitaniumBoltLocations.ASYANICA_ROOFTOPS_1, SACLocationType.TITANIUM_BOLT, _BASE_RULE),
    SACLocation(SACMissionLocations.ASYANICA_ROOFTOPS_COMPLETE, SACLocationType.CASE_COMPLETE, _BASE_RULE),
    SACLocation(SACMissionLocations.ASYANICA_ROOFTOPS_NUMBER_WOO_WORKS_FOR, SACLocationType.MISSION, _OMNIKEY),
    SACLocation(SACSkillPointLocations.ASYANICA_ROOFTOPS_ROBOT_FINDS_NINJA, SACLocationType.SKILL_POINT, _OMNIKEY),
    SACLocation(SACSkillPointLocations.ASYANICA_ROOFTOPS_BLACK_TIE_AFFAIR, SACLocationType.SKILL_POINT, _OMNIKEY),
    SACLocation(SACSkillPointLocations.ASYANICA_ROOFTOPS_LIKE_THE_WIND, SACLocationType.SKILL_POINT, _OMNIKEY),
    SACLocation(SACKeycardLocations.RED_KEYCARD, SACLocationType.KEYCARD, _OMNIKEY),
    SACLocation(SACAlienCodeLocations.ASYANICA_ROOFTOPS_JHAIROS_SECRET,
                SACLocationType.ALIEN_CODE, Has(SACClankGadgets.THERM_OPTIC_SHADES) & _OMNIKEY),
    SACLocation(SACAlienCodeLocations.ASYANICA_ROOFTOPS_GILBERTS_SECRET,
                SACLocationType.ALIEN_CODE, Has(SACClankGadgets.THERM_OPTIC_SHADES) & _OMNIKEY),
    SACLocation(SACAlienCodeLocations.ASYANICA_ROOFTOPS_RICARDOS_SECRET,
                SACLocationType.ALIEN_CODE, Has(SACClankGadgets.THERM_OPTIC_SHADES) & _OMNIKEY),
))

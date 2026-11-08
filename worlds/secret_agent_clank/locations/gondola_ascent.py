from rule_builder.rules import HasAll

from ..constants import (
    SACAlienCodeLocations,
    SACCases,
    SACClankGadgets,
    SACClankWeapons,
    SACCutsceneLocations,
    SACMissionLocations,
    SACSkillPointLocations,
    SACTitaniumBoltLocations,
)
from .model import CaseRegion, SACLocation, SACLocationType

_BASE_ITEMS = (SACClankGadgets.JETBOOTS, SACClankWeapons.TANGLEVINE)
_BASE = HasAll(*_BASE_ITEMS)
_OMNIKEY = HasAll(*_BASE_ITEMS, SACClankGadgets.OMNIKEY)

REGION = CaseRegion(SACCases.GONDOLA_ASCENT, (
    SACLocation(SACTitaniumBoltLocations.GONDOLA_ASCENT_1, SACLocationType.TITANIUM_BOLT, _BASE, flag_bit=0),
    SACLocation(SACMissionLocations.GONDOLA_ASCENT_COMPLETE, SACLocationType.CASE_COMPLETE, _BASE),
    SACLocation(SACMissionLocations.GONDOLA_ASCENT_GET_A_LIFT, SACLocationType.MISSION, _OMNIKEY),
    SACLocation(SACSkillPointLocations.GONDOLA_ASCENT_STEEL_RAIN,
                SACLocationType.SKILL_POINT, HasAll(*_BASE_ITEMS, SACClankWeapons.HOLOKNUCKLES)),
    SACLocation(SACCutsceneLocations.GONDOLA_ASCENT_FINISH_GONDOLA_CUTSCENE, SACLocationType.CUTSCENE, _OMNIKEY),
    SACLocation(SACAlienCodeLocations.GONDOLA_ASCENT_LEVITICUS_SECRET,
                SACLocationType.ALIEN_CODE, HasAll(*_BASE_ITEMS, SACClankGadgets.THERM_OPTIC_SHADES), flag_bit=0),
    SACLocation(SACAlienCodeLocations.GONDOLA_ASCENT_CARLS_SECRET,
                SACLocationType.ALIEN_CODE, HasAll(*_BASE_ITEMS, SACClankGadgets.THERM_OPTIC_SHADES), flag_bit=1),
    SACLocation(SACAlienCodeLocations.GONDOLA_ASCENT_JESS_SECRET,
                SACLocationType.ALIEN_CODE, HasAll(*_BASE_ITEMS, SACClankGadgets.THERM_OPTIC_SHADES), flag_bit=2),
))

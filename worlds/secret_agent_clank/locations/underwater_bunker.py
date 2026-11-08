from rule_builder.rules import Has, HasAll, HasAny

from ..constants import (
    SACAlienCodeLocations,
    SACCases,
    SACClankGadgets,
    SACClankWeapons,
    SACMissionLocations,
    SACSkillPointLocations,
    SACTitaniumBoltLocations,
)
from .model import CaseRegion, SACLocation, SACLocationType

_BASE_ITEMS = (SACClankGadgets.JETBOOTS, SACClankGadgets.OMNIKEY, SACClankWeapons.THROWTIE)
_VESSUPS_SECRET_LOGIC = (Has(SACClankGadgets.THERM_OPTIC_SHADES) &
                         HasAny(SACClankWeapons.FLAMETHROWERPEN, SACClankGadgets.BLACK_OUT_PEN))
_BASE = HasAll(*_BASE_ITEMS) & HasAny(SACClankWeapons.FLAMETHROWERPEN, SACClankGadgets.BLACK_OUT_PEN)
_BASE_SHADES = _BASE & Has(SACClankGadgets.THERM_OPTIC_SHADES)

REGION = CaseRegion(SACCases.UNDERWATER_BUNKER, (
    SACLocation(SACTitaniumBoltLocations.UNDERWATER_BUNKER_1, SACLocationType.TITANIUM_BOLT, _BASE, flag_bit=0),
    SACLocation(SACMissionLocations.UNDERWATER_BUNKER_COMPLETE, SACLocationType.CASE_COMPLETE, _BASE),
    SACLocation(SACMissionLocations.UNDERWATER_BUNKER_CLANK_UNDER_GLASS, SACLocationType.MISSION, _BASE),
    SACLocation(SACSkillPointLocations.UNDERWATER_BUNKER_LEET_HAXXOR, SACLocationType.SKILL_POINT, _BASE),
    SACLocation(SACSkillPointLocations.UNDERWATER_BUNKER_RUST_PROOF, SACLocationType.SKILL_POINT, _BASE),
    SACLocation(SACSkillPointLocations.UNDERWATER_BUNKER_IM_NOT_THERE,
                SACLocationType.SKILL_POINT, HasAll(*_BASE_ITEMS, SACClankGadgets.BLACK_OUT_PEN)),
    SACLocation(SACAlienCodeLocations.UNDERWATER_BUNKER_VESSUPS_SECRET,
                SACLocationType.ALIEN_CODE, _VESSUPS_SECRET_LOGIC, flag_bit=0),
    SACLocation(SACAlienCodeLocations.UNDERWATER_BUNKER_ADAMS_SECRET,
                SACLocationType.ALIEN_CODE, _BASE_SHADES, flag_bit=1),
    SACLocation(SACAlienCodeLocations.UNDERWATER_BUNKER_JEFFS_SECRET,
                SACLocationType.ALIEN_CODE, _BASE_SHADES, flag_bit=2),
))

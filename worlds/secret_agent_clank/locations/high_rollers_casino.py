"""High-Rollers Casino: the case region and every location in it, with its access rule."""
from rule_builder.rules import Has, True_
from ..constants.clank_gadgets import SACClankWeapons

from ..constants import (
    SACAlienCodeLocations,
    SACCases,
    SACClankGadgets,
    SACCutsceneLocations,
    SACMissionLocations,
    SACPickups,
    SACSkillPointLocations,
    SACTitaniumBoltLocations,
)
from .model import CaseRegion, SACLocation, SACLocationType

_BASE = Has(SACClankGadgets.HOLOMONOCLE)
_complete = _BASE & Has(SACClankWeapons.CUFFLINK)

REGION = CaseRegion(SACCases.HIGH_ROLLERS_CASINO, (
    SACLocation(SACPickups.HIGH_ROLLERS_CASINO_HOLO_MONOCLE, SACLocationType.CLANK_GADGET),
    SACLocation(SACTitaniumBoltLocations.HIGH_ROLLERS_CASINO_1,
                SACLocationType.TITANIUM_BOLT, _BASE & Has(SACClankGadgets.OMNIKEY)),
    SACLocation(SACMissionLocations.HIGH_ROLLERS_CASINO_COMPLETE, SACLocationType.CASE_COMPLETE, _complete),
    SACLocation(SACMissionLocations.HIGH_ROLLERS_CASINO_EXPLORE_PARADISE, SACLocationType.MISSION, _BASE),
    SACLocation(SACMissionLocations.HIGH_ROLLERS_CASINO_PARADISE_EXPLOITED, SACLocationType.MISSION, _BASE),
    SACLocation(SACSkillPointLocations.HIGH_ROLLERS_CASINO_BEAT_THE_HOUSE, SACLocationType.SKILL_POINT, _BASE),
    SACLocation(SACCutsceneLocations.HIGH_ROLLERS_CASINO_ENTER_CUTSCENE, SACLocationType.CUTSCENE, True_()),
    SACLocation(SACCutsceneLocations.HIGH_ROLLERS_CASINO_COMPLETE_CUTSCENE, SACLocationType.CUTSCENE, _complete),
    SACLocation(SACAlienCodeLocations.HIGH_ROLLERS_CASINO_COLINS_SECRET,
                SACLocationType.ALIEN_CODE, Has(SACClankGadgets.THERM_OPTIC_SHADES)),
    SACLocation(SACAlienCodeLocations.HIGH_ROLLERS_CASINO_SHANES_SECRET,
                SACLocationType.ALIEN_CODE, _BASE & Has(SACClankGadgets.THERM_OPTIC_SHADES)),
    SACLocation(SACAlienCodeLocations.HIGH_ROLLERS_CASINO_THE_PING_PONG_SECRET,
                SACLocationType.ALIEN_CODE, _BASE & Has(SACClankGadgets.THERM_OPTIC_SHADES)),
))

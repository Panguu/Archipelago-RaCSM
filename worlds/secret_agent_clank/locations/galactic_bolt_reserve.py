"""Galactic Bolt Reserve: the case region and every location in it, with its access rule."""
from rule_builder.rules import Has, HasAll

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

_BASE = HasAll(SACClankWeapons.CUFFLINK, SACClankWeapons.THROWTIE, SACClankGadgets.JETBOOTS)
_OMNIKEY = _BASE & Has(SACClankGadgets.OMNIKEY)
_HOLOMONICLE = _OMNIKEY & Has(SACClankGadgets.HOLOMONOCLE)
STEALTH_RULE = _OMNIKEY

REGION = CaseRegion(SACCases.GALACTIC_BOLT_RESERVE, (
    SACLocation(SACTitaniumBoltLocations.GALACTIC_BOLT_RESERVE_1, SACLocationType.TITANIUM_BOLT, _BASE),
    SACLocation(SACTitaniumBoltLocations.GALACTIC_BOLT_RESERVE_2, SACLocationType.TITANIUM_BOLT, _OMNIKEY),
    SACLocation(SACTitaniumBoltLocations.GALACTIC_BOLT_RESERVE_3, SACLocationType.TITANIUM_BOLT, _HOLOMONICLE),
    SACLocation(SACMissionLocations.GALACTIC_BOLT_RESERVE_COMPLETE, SACLocationType.CASE_COMPLETE, _HOLOMONICLE),
    SACLocation(SACMissionLocations.GALACTIC_BOLT_RESERVE_HARD_CURRENCY, SACLocationType.MISSION, _OMNIKEY),
    SACLocation(SACMissionLocations.GALACTIC_BOLT_RESERVE_THE_BIG_HEIST, SACLocationType.MISSION, _HOLOMONICLE),
    SACLocation(SACSkillPointLocations.GALACTIC_BOLT_RESERVE_WITH_INTEREST, SACLocationType.SKILL_POINT, _HOLOMONICLE),
    SACLocation(SACSkillPointLocations.GALACTIC_BOLT_RESERVE_ANDROIDS_IN_DISGUISE,
                SACLocationType.SKILL_POINT, _HOLOMONICLE),
    SACLocation(SACCutsceneLocations.GALACTIC_BOLT_RESERVE_ENTER_CUTSCENE, SACLocationType.CUTSCENE),
    SACLocation(SACCutsceneLocations.GALACTIC_BOLT_RESERVE_COMPLETE_CUTSCENE, SACLocationType.CUTSCENE, _HOLOMONICLE),
    SACLocation(SACAlienCodeLocations.GALACTIC_BOLT_RESERVE_AVERYS_SECRET,
                SACLocationType.ALIEN_CODE, _BASE & Has(SACClankGadgets.THERM_OPTIC_SHADES)),
    SACLocation(SACAlienCodeLocations.GALACTIC_BOLT_RESERVE_LESLEYS_SECRET,
                SACLocationType.ALIEN_CODE, _OMNIKEY & Has(SACClankGadgets.THERM_OPTIC_SHADES)),
    SACLocation(SACAlienCodeLocations.GALACTIC_BOLT_RESERVE_DAVES_SECRET,
                SACLocationType.ALIEN_CODE, _HOLOMONICLE & Has(SACClankGadgets.THERM_OPTIC_SHADES)),
))

from rule_builder.rules import Has, HasAll

from ..constants import (
    SACAlienCodeLocations,
    SACCases,
    SACClankGadgets,
    SACClankWeapons,
    SACCutsceneLocations,
    SACMissionLocations,
    SACPickups,
    SACSkillPointLocations,
    SACTitaniumBoltLocations,
    SACVendor,
)
from ..rules import ProgressiveChallengeModeRule, VendorCaseRule
from .model import CaseRegion, SACLocation, SACLocationType

_BASE_ITEMS = (SACClankWeapons.CUFFLINK, SACClankGadgets.OMNIKEY)
_BRIEFCASE_ITEMS = (SACClankWeapons.FLAMETHROWERPEN, SACClankWeapons.CUFFLINK)
_BRIEFCASE_JETBOOTS_ITEMS = (*_BRIEFCASE_ITEMS, SACClankGadgets.JETBOOTS)
_BASE = HasAll(*_BASE_ITEMS)
_BRIEFCASE_PATH = HasAll(*_BRIEFCASE_ITEMS)
_BRIEFCASE_JETBOOTS = HasAll(*_BRIEFCASE_JETBOOTS_ITEMS)
_FINISH = HasAll(*_BRIEFCASE_JETBOOTS_ITEMS, SACClankGadgets.OMNIKEY)

_VENDOR = VendorCaseRule(SACCases.VENANTONIO_LABS)
_CHALLENGE_VENDOR = _VENDOR & ProgressiveChallengeModeRule()

REGION = CaseRegion(SACCases.VENANTONIO_LABS, (
    SACLocation(SACPickups.VENANTONIO_LABS_BLOWTORCH_BRIEFCASE, SACLocationType.CLANK_WEAPON, _BASE),
    SACLocation(SACTitaniumBoltLocations.VENANTONIO_LABS_1, SACLocationType.TITANIUM_BOLT,
                HasAll(*_BASE_ITEMS, SACClankWeapons.FLAMETHROWERPEN), flag_bit=0),
    SACLocation(SACTitaniumBoltLocations.VENANTONIO_LABS_2, SACLocationType.TITANIUM_BOLT, _BRIEFCASE_JETBOOTS,
                flag_bit=1),
    SACLocation(SACMissionLocations.VENANTONIO_LABS_COMPLETE, SACLocationType.CASE_COMPLETE, _FINISH),
    SACLocation(SACMissionLocations.VENANTONIO_LABS_CRASHING_THE_PARTY, SACLocationType.MISSION, _FINISH),
    SACLocation(SACMissionLocations.VENANTONIO_LABS_OUT_OF_THE_FRYING_PAN, SACLocationType.MISSION, _FINISH),
    SACLocation(SACSkillPointLocations.VENANTONIO_LABS_ALL_SLIME_MUST_BURN,
                SACLocationType.SKILL_POINT, HasAll(*_BASE_ITEMS, SACClankWeapons.FLAMETHROWERPEN)),
    SACLocation(SACSkillPointLocations.VENANTONIO_LABS_RAMMING_SPEED, SACLocationType.SKILL_POINT, _BRIEFCASE_PATH),
    SACLocation(SACCutsceneLocations.VENANTONIO_LABS_ENTER_CUTSCENE, SACLocationType.CUTSCENE),
    SACLocation(SACCutsceneLocations.VENANTONIO_LABS_OPEN_GREEN_DOOR_CUTSCENE, SACLocationType.CUTSCENE),
    SACLocation(SACCutsceneLocations.VENANTONIO_LABS_COMPLETE_CUTSCENE, SACLocationType.CUTSCENE, _FINISH),
    SACLocation(SACAlienCodeLocations.VENANTONIO_LABS_GERARDS_SECRET,
                SACLocationType.ALIEN_CODE, Has(SACClankGadgets.THERM_OPTIC_SHADES), flag_bit=0),
    SACLocation(SACAlienCodeLocations.VENANTONIO_LABS_ALEXS_SECRET,
                SACLocationType.ALIEN_CODE, HasAll(*_BRIEFCASE_JETBOOTS_ITEMS, SACClankGadgets.THERM_OPTIC_SHADES),
                flag_bit=1),
    SACLocation(SACAlienCodeLocations.VENANTONIO_LABS_HAROONS_SECRET,
                SACLocationType.ALIEN_CODE, HasAll(*_BRIEFCASE_JETBOOTS_ITEMS, SACClankGadgets.THERM_OPTIC_SHADES),
                flag_bit=2),
    SACLocation(SACVendor.VENANTONIO_LABS_PLASMA_WHIP, SACLocationType.VENDOR, _VENDOR),
    SACLocation(SACVendor.VENANTONIO_LABS_CLANK_FU_HOT_FOOT, SACLocationType.VENDOR, _VENDOR),
    SACLocation(SACVendor.VENANTONIO_LABS_THUNDERSTORM_UMBRELLA, SACLocationType.VENDOR, _VENDOR),
    SACLocation(SACVendor.VENANTONIO_LABS_PROTO_LIGHTNING_ROD, SACLocationType.TITAN_VENDOR, _CHALLENGE_VENDOR),
    SACLocation(SACVendor.VENANTONIO_LABS_PROTO_HELLFIRE_HAVERSACK, SACLocationType.TITAN_VENDOR, _CHALLENGE_VENDOR),
    SACLocation(SACVendor.VENANTONIO_LABS_TITAN_PLASMA_CORD, SACLocationType.TITAN_VENDOR, _CHALLENGE_VENDOR),
    SACLocation(SACVendor.CHALLENGE_MODE_BLOWTORCH_BRIEFCASE_MOLTEN_BOLT,
                SACLocationType.MOD_VENDOR, _CHALLENGE_VENDOR),
    SACLocation(SACVendor.CHALLENGE_MODE_THUNDERSTORM_UMBRELLA_XENOS_CAPACITOR,
                SACLocationType.MOD_VENDOR, _CHALLENGE_VENDOR),
    SACLocation(SACVendor.CHALLENGE_MODE_THUNDERSTORM_UMBRELLA_THUNDERCLOUD,
                SACLocationType.MOD_VENDOR, _CHALLENGE_VENDOR),
))

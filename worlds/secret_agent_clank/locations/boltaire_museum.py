from rule_builder.rules import Has, HasAll, HasAny

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

_FINISH_MISSION = HasAll(SACClankGadgets.BLACK_OUT_PEN, SACClankGadgets.JETBOOTS)
_REACH_INSIDE_MUSEUM = HasAll(SACClankGadgets.BLACK_OUT_PEN, HasAny(SACClankGadgets.JETBOOTS, SACClankWeapons.THROWTIE))


_VENDOR = VendorCaseRule(SACCases.BOLTAIRE_MUSEUM)
_CHALLENGE_VENDOR = _VENDOR & ProgressiveChallengeModeRule()

REGION = CaseRegion(SACCases.BOLTAIRE_MUSEUM, (
    SACLocation(SACPickups.BOLTAIRE_MUSEUM_DUAL_LACERATORS,
                SACLocationType.RATCHET_WEAPON, Has(SACClankGadgets.BLACK_OUT_PEN)),
    SACLocation(SACPickups.BOLTAIRE_MUSEUM_TIE_A_RANG, SACLocationType.CLANK_WEAPON),
    SACLocation(SACPickups.BOLTAIRE_MUSEUM_JET_BOOTS, SACLocationType.CLANK_GADGET, _FINISH_MISSION),
    SACLocation(SACPickups.BOLTAIRE_MUSEUM_BLACKOUT_PEN, SACLocationType.GADGET_PICKUP),
    SACLocation(SACPickups.BOLTAIRE_MUSEUM_THERM_OPTIC_SHADES, SACLocationType.GADGET_PICKUP, ProgressiveChallengeModeRule()),
    SACLocation(SACTitaniumBoltLocations.BOLTAIRE_MUSEUM_1,
                SACLocationType.TITANIUM_BOLT, Has(SACClankGadgets.JETBOOTS), flag_bit=0),
    SACLocation(SACTitaniumBoltLocations.BOLTAIRE_MUSEUM_2,
                SACLocationType.TITANIUM_BOLT, HasAll(SACClankGadgets.JETBOOTS, SACClankGadgets.BLACK_OUT_PEN),
                flag_bit=1),
    SACLocation(SACMissionLocations.BOLTAIRE_MUSEUM_COMPLETE, SACLocationType.CASE_COMPLETE, _FINISH_MISSION),
    SACLocation(SACMissionLocations.BOLTAIRE_MUSEUM_ESCAPE_THE_RAVINE, SACLocationType.MISSION),
    SACLocation(SACMissionLocations.BOLTAIRE_MUSEUM_GET_INSIDE_THE_MUSEUM, SACLocationType.MISSION),
    SACLocation(SACMissionLocations.BOLTAIRE_MUSEUM_NOT_THE_GUIDED_TOUR, SACLocationType.MISSION, _FINISH_MISSION),
    SACLocation(SACSkillPointLocations.BOLTAIRE_MUSEUM_FURIOUS_FISTS, SACLocationType.SKILL_POINT, _FINISH_MISSION),
    SACLocation(SACSkillPointLocations.BOLTAIRE_MUSEUM_SILENT_NIGHT, SACLocationType.SKILL_POINT, _FINISH_MISSION),
    SACLocation(SACCutsceneLocations.BOLTAIRE_MUSEUM_ENTER_CUTSCENE, SACLocationType.CUTSCENE),
    SACLocation(SACAlienCodeLocations.BOLTAIRE_MUSEUM_THE_LEGENDS,
                SACLocationType.ALIEN_CODE, Has(SACClankGadgets.THERM_OPTIC_SHADES), flag_bit=1),
    SACLocation(SACAlienCodeLocations.BOLTAIRE_MUSEUM_RONNS_SECRET,
                SACLocationType.ALIEN_CODE, HasAll(SACClankGadgets.BLACK_OUT_PEN, SACClankGadgets.THERM_OPTIC_SHADES),
                flag_bit=0),
    SACLocation(SACAlienCodeLocations.BOLTAIRE_MUSEUM_BENS_SECRET,
                SACLocationType.ALIEN_CODE, _REACH_INSIDE_MUSEUM & Has(SACClankGadgets.THERM_OPTIC_SHADES),
                flag_bit=2),
    SACLocation(SACVendor.BOLTAIRE_MUSEUM_HOLO_KNUCKLES, SACLocationType.VENDOR, _VENDOR),
    SACLocation(SACVendor.BOLTAIRE_MUSEUM_CLANK_FU_KICK, SACLocationType.VENDOR, _VENDOR),
    SACLocation(SACVendor.BOLTAIRE_MUSEUM_PROTO_WHIRLWIND_THROWTIE, SACLocationType.TITAN_VENDOR, _CHALLENGE_VENDOR),
    SACLocation(SACVendor.BOLTAIRE_MUSEUM_CLANK_PROTO_HARDLIGHT_FIST, SACLocationType.TITAN_VENDOR, _CHALLENGE_VENDOR),
    SACLocation(SACVendor.BOLTAIRE_MUSEUM_TITAN_DUAL_VINDICATORS, SACLocationType.TITAN_VENDOR, _CHALLENGE_VENDOR),
    SACLocation(SACVendor.CHALLENGE_MODE_RYNO, SACLocationType.VENDOR, _CHALLENGE_VENDOR),
    SACLocation(SACVendor.CHALLENGE_MODE_HOT_FOOT_21_BETA, SACLocationType.VENDOR, _CHALLENGE_VENDOR),
))

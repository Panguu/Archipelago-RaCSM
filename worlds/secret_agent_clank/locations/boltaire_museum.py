"""Boltaire Museum: the case region and every location in it, with its access rule."""
from typing import TYPE_CHECKING

from rule_builder.rules import Has, HasAll, Rule

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
)
from ..constants.challenge_mode import PROGRESSIVE_CHALLENGE_MODE
from .model import CaseRegion, SACLocation, SACLocationType

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld

_FINISH_MISSION = HasAll(SACClankGadgets.BLACK_OUT_PEN, SACClankWeapons.THROWTIE, SACClankGadgets.JETBOOTS)


def _challenge_mode(world: "SecretAgentClankWorld") -> "Rule | None":
    """The shades pickup only spawns in challenge mode, which progressive seeds must unlock first."""
    return Has(PROGRESSIVE_CHALLENGE_MODE) if world.options.progressive_challenge_mode else None


REGION = CaseRegion(SACCases.BOLTAIRE_MUSEUM, (
    SACLocation(SACPickups.BOLTAIRE_MUSEUM_DUAL_LACERATORS,
                SACLocationType.RATCHET_WEAPON, Has(SACClankGadgets.BLACK_OUT_PEN)),
    SACLocation(SACPickups.BOLTAIRE_MUSEUM_TIE_A_RANG, SACLocationType.CLANK_WEAPON),
    SACLocation(SACPickups.BOLTAIRE_MUSEUM_JET_BOOTS, SACLocationType.CLANK_GADGET, _FINISH_MISSION),
    SACLocation(SACPickups.BOLTAIRE_MUSEUM_BLACKOUT_PEN, SACLocationType.GADGET_PICKUP),
    SACLocation(SACPickups.BOLTAIRE_MUSEUM_THERM_OPTIC_SHADES, SACLocationType.GADGET_PICKUP, _challenge_mode),
    SACLocation(SACTitaniumBoltLocations.BOLTAIRE_MUSEUM_1,
                SACLocationType.TITANIUM_BOLT, Has(SACClankGadgets.JETBOOTS)),
    SACLocation(SACTitaniumBoltLocations.BOLTAIRE_MUSEUM_2,
                SACLocationType.TITANIUM_BOLT, HasAll(SACClankGadgets.JETBOOTS, SACClankGadgets.BLACK_OUT_PEN)),
    SACLocation(SACMissionLocations.BOLTAIRE_MUSEUM_COMPLETE, SACLocationType.CASE_COMPLETE),
    SACLocation(SACMissionLocations.BOLTAIRE_MUSEUM_ESCAPE_THE_RAVINE, SACLocationType.MISSION),
    SACLocation(SACMissionLocations.BOLTAIRE_MUSEUM_GET_INSIDE_THE_MUSEUM, SACLocationType.MISSION),
    SACLocation(SACMissionLocations.BOLTAIRE_MUSEUM_NOT_THE_GUIDED_TOUR, SACLocationType.MISSION, _FINISH_MISSION),
    SACLocation(SACSkillPointLocations.BOLTAIRE_MUSEUM_FURIOUS_FISTS, SACLocationType.SKILL_POINT, _FINISH_MISSION),
    SACLocation(SACSkillPointLocations.BOLTAIRE_MUSEUM_SILENT_NIGHT, SACLocationType.SKILL_POINT, _FINISH_MISSION),
    SACLocation(SACCutsceneLocations.BOLTAIRE_MUSEUM_ENTER_CUTSCENE, SACLocationType.CUTSCENE),
    SACLocation(SACAlienCodeLocations.BOLTAIRE_MUSEUM_THE_LEGENDS,
                SACLocationType.ALIEN_CODE, Has(SACClankGadgets.THERM_OPTIC_SHADES)),
    SACLocation(SACAlienCodeLocations.BOLTAIRE_MUSEUM_RONNS_SECRET,
                SACLocationType.ALIEN_CODE, _FINISH_MISSION & Has(SACClankGadgets.THERM_OPTIC_SHADES)),
    SACLocation(SACAlienCodeLocations.BOLTAIRE_MUSEUM_BENS_SECRET,
                SACLocationType.ALIEN_CODE, _FINISH_MISSION & Has(SACClankGadgets.THERM_OPTIC_SHADES)),
))

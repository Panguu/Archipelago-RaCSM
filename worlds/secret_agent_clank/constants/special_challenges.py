"""String constants for Special Challenge locations -- the Special Missions-operative counterpart to constants/gadgetbot_challenges.py's Gadgetbot Challenges (same structural pattern: addresses recorded individually, each a plain 0/1 byte -- see SPECIAL_CHALLENGES below, CONFIRMED live for every entry so far)."""

from dataclasses import dataclass

from .planets import SACCases
from .types import CaseStructure, SACTags, group_by_case, with_display_names


@dataclass(frozen=True)
class SACSpecialChallenges:
    """String constants for Special Challenge event titles (short form only -- see SPECIAL_CHALLENGES below for which case/address each belongs to)."""

    VEHICLE_GREAT_ESCAPE = "Vehicle: Great Escape"
    VEHICLE_SPEEDBOATING = "Vehicle: Speedboating"
    VEHICLE_THREADING_THE_NEEDLE = "Vehicle: Threading the Needle"

    VEHICLE_CHASING_A_LEAD = "Vehicle: Chasing a Lead"
    VEHICLE_RUSH_HOUR = "Vehicle: Rush Hour"
    VEHICLE_DRIVING_TEST = "Vehicle: Driving Test"

    VEHICLE_VILLA_ESCAPE = "Vehicle: Villa Escape"
    VEHICLE_BLACK_DIAMOND = "Vehicle: Black Diamond"
    VEHICLE_GO_FOR_THE_GOLD = "Vehicle: Go for the Gold"


_RAW_SPECIAL_CHALLENGES: tuple[CaseStructure, ...] = (
    CaseStructure(
        SACCases.VENANTONIO_CANALS, SACSpecialChallenges.VEHICLE_GREAT_ESCAPE, SACTags.SPECIAL_CHALLENGE,
        event_flag=0b00000001, event_address=0x206C9E,
    ),
    CaseStructure(
        SACCases.VENANTONIO_CANALS, SACSpecialChallenges.VEHICLE_SPEEDBOATING, SACTags.SPECIAL_CHALLENGE,
        event_flag=0b00000001, event_address=0x206C9F,
    ),
    CaseStructure(
        SACCases.VENANTONIO_CANALS, SACSpecialChallenges.VEHICLE_THREADING_THE_NEEDLE, SACTags.SPECIAL_CHALLENGE,
        event_flag=0b00000001, event_address=0x206CA0,
    ),
    CaseStructure(
        SACCases.DAMS_EDGE_HYDRANO, SACSpecialChallenges.VEHICLE_CHASING_A_LEAD, SACTags.SPECIAL_CHALLENGE,
        event_flag=0b00000001, event_address=0x206CA1,
    ),
    CaseStructure(
        SACCases.DAMS_EDGE_HYDRANO, SACSpecialChallenges.VEHICLE_RUSH_HOUR, SACTags.SPECIAL_CHALLENGE,
        event_flag=0b00000001, event_address=0x206CA2,
    ),
    CaseStructure(
        SACCases.DAMS_EDGE_HYDRANO, SACSpecialChallenges.VEHICLE_DRIVING_TEST, SACTags.SPECIAL_CHALLENGE,
        event_flag=0b00000001, event_address=0x206CA3,
    ),
    CaseStructure(
        SACCases.GLACIARA_SKI_SLOPES, SACSpecialChallenges.VEHICLE_VILLA_ESCAPE, SACTags.SPECIAL_CHALLENGE,
        event_flag=0b00000001, event_address=0x206C9B,
    ),
    CaseStructure(
        SACCases.GLACIARA_SKI_SLOPES, SACSpecialChallenges.VEHICLE_BLACK_DIAMOND, SACTags.SPECIAL_CHALLENGE,
        event_flag=0b00000001, event_address=0x206C9C,
    ),
    CaseStructure(
        SACCases.GLACIARA_SKI_SLOPES, SACSpecialChallenges.VEHICLE_GO_FOR_THE_GOLD, SACTags.SPECIAL_CHALLENGE,
        event_flag=0b00000001, event_address=0x206C9D,
    ),
)


@dataclass(frozen=True)
class SACSpecialChallengeLocations:
    VENANTONIO_CANALS_VEHICLE_GREAT_ESCAPE = "Venantonio (Special Missions) - Venantonio Canals: Great Escape"
    VENANTONIO_CANALS_VEHICLE_SPEEDBOATING = "Venantonio (Special Missions) - Venantonio Canals: Speedboating"
    VENANTONIO_CANALS_VEHICLE_THREADING_THE_NEEDLE = "Venantonio (Special Missions) - Venantonio Canals: Threading the Needle"
    DAMS_EDGE_HYDRANO_VEHICLE_CHASING_A_LEAD = "Hydrano (Special Missions) - Dam's Edge, Hydrano: Chasing a Lead"
    DAMS_EDGE_HYDRANO_VEHICLE_RUSH_HOUR = "Hydrano (Special Missions) - Dam's Edge, Hydrano: Rush Hour"
    DAMS_EDGE_HYDRANO_VEHICLE_DRIVING_TEST = "Hydrano (Special Missions) - Dam's Edge, Hydrano: Driving Test"
    GLACIARA_SKI_SLOPES_VEHICLE_VILLA_ESCAPE = "Glaciara (Special Missions) - Glaciara, Ski Slopes: Villa Escape"
    GLACIARA_SKI_SLOPES_VEHICLE_BLACK_DIAMOND = "Glaciara (Special Missions) - Glaciara, Ski Slopes: Black Diamond"
    GLACIARA_SKI_SLOPES_VEHICLE_GO_FOR_THE_GOLD = "Glaciara (Special Missions) - Glaciara, Ski Slopes: Go for the Gold"


SPECIAL_CHALLENGES: tuple[CaseStructure, ...] = with_display_names(
    _RAW_SPECIAL_CHALLENGES, SACSpecialChallengeLocations)

# Case.name -> its known Special Challenges' full display names, derived
# from SPECIAL_CHALLENGES above. Order is declaration order (display/
# iteration convenience) -- it does NOT imply anything about address layout.
SPECIAL_CHALLENGES_BY_CASE: dict[str, tuple[str, ...]] = group_by_case(SPECIAL_CHALLENGES)

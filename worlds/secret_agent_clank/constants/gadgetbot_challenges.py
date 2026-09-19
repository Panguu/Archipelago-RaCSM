"""String constants for Gadgetbot Challenge locations."""

from dataclasses import dataclass

from .planets import SACCases
from .types import CaseStructure, SACTags, group_by_case, with_display_names


@dataclass(frozen=True)
class SACGadgetbotChallenges:
    """String constants for Gadgetbot Challenge event titles (short form only -- see GADGETBOT_CHALLENGES below for which case/address each belongs to)."""

    RESCUE_CLANK = "Rescue Clank"
    WORKING_DOWN = "Working Down"
    GREAT_DIVIDE = "Great Divide"

    VAULTBREAKERS = "Vaultbreakers"
    DARK_HELMET = "Dark Helmet"
    GO_LONG = "Go Long"

    KNOCKIN_ON_KLUNKS_DOOR = "Knockin' on Klunk's Door"
    MISSION_POSSIBLE = "Mission: Possible"


_RAW_GADGETBOT_CHALLENGES: tuple[CaseStructure, ...] = (
    CaseStructure(
        SACCases.ROOFTOP_DEATHTRAP, SACGadgetbotChallenges.RESCUE_CLANK, SACTags.GADGETBOT_CHALLENGE,
        event_flag=0b00000001, event_address=0x206C7A,
    ),
    CaseStructure(
        SACCases.ROOFTOP_DEATHTRAP, SACGadgetbotChallenges.WORKING_DOWN, SACTags.GADGETBOT_CHALLENGE,
        event_flag=0b00000001, event_address=0x206C7B,
    ),
    CaseStructure(
        SACCases.ROOFTOP_DEATHTRAP, SACGadgetbotChallenges.GREAT_DIVIDE, SACTags.GADGETBOT_CHALLENGE,
        event_flag=0b00000001, event_address=0x206C7C,
    ),
    CaseStructure(
        SACCases.INSIDE_THE_A_EYE, SACGadgetbotChallenges.VAULTBREAKERS, SACTags.GADGETBOT_CHALLENGE,
        event_flag=0b00000001, event_address=0x206C7F,
    ),
    CaseStructure(
        SACCases.INSIDE_THE_A_EYE, SACGadgetbotChallenges.DARK_HELMET, SACTags.GADGETBOT_CHALLENGE,
        event_flag=0b00000001, event_address=0x206C80,
    ),
    CaseStructure(
        SACCases.INSIDE_THE_A_EYE, SACGadgetbotChallenges.GO_LONG, SACTags.GADGETBOT_CHALLENGE,
        event_flag=0b00000001, event_address=0x206C81,
    ),
    CaseStructure(
        SACCases.BULKHEAD_LOCK, SACGadgetbotChallenges.KNOCKIN_ON_KLUNKS_DOOR, SACTags.GADGETBOT_CHALLENGE,
        event_flag=0b00000001, event_address=0x206C83,
    ),
    CaseStructure(
        SACCases.BULKHEAD_LOCK, SACGadgetbotChallenges.MISSION_POSSIBLE, SACTags.GADGETBOT_CHALLENGE,
        event_flag=0b00000001, event_address=0x206C84,
    ),
)


@dataclass(frozen=True)
class SACGadgetbotChallengeLocations:
    ROOFTOP_DEATHTRAP_RESCUE_CLANK = "Asyanica (Gadgetbots) - Rooftop Deathtrap: Rescue Clank"
    ROOFTOP_DEATHTRAP_WORKING_DOWN = "Asyanica (Gadgetbots) - Rooftop Deathtrap: Working Down"
    ROOFTOP_DEATHTRAP_GREAT_DIVIDE = "Asyanica (Gadgetbots) - Rooftop Deathtrap: Great Divide"
    INSIDE_THE_A_EYE_VAULTBREAKERS = "Fort Sprocket (Gadgetbots) - Inside the A-Eye: Vaultbreakers"
    INSIDE_THE_A_EYE_DARK_HELMET = "Fort Sprocket (Gadgetbots) - Inside the A-Eye: Dark Helmet"
    INSIDE_THE_A_EYE_GO_LONG = "Fort Sprocket (Gadgetbots) - Inside the A-Eye: Go Long"
    BULKHEAD_LOCK_KNOCKIN_ON_KLUNKS_DOOR = "Underwater Base (Gadgetbots) - Bulkhead Lock: Knockin' on Klunk's Door"
    BULKHEAD_LOCK_MISSION_POSSIBLE = "Underwater Base (Gadgetbots) - Bulkhead Lock: Mission: Possible"


GADGETBOT_CHALLENGES: tuple[CaseStructure, ...] = with_display_names(
    _RAW_GADGETBOT_CHALLENGES, SACGadgetbotChallengeLocations)

# Case.name -> its known Gadgetbot Challenges' full display names, derived
# from GADGETBOT_CHALLENGES above. Order is declaration order
# (display/iteration convenience) -- it does NOT imply anything about
# address layout.
GADGETBOT_CHALLENGES_BY_CASE: dict[str, tuple[str, ...]] = group_by_case(GADGETBOT_CHALLENGES)

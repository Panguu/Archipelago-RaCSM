"""Ratchet arena challenge names in native per-case challenge order."""

from dataclasses import dataclass

from .planets import SACCases
from .types import CaseStructure, group_by_case


@dataclass(frozen=True)
class SACRatchetChallenges:
    """String constants for Ratchet Challenge event titles (short form only -- see RATCHET_CHALLENGES below for which case/address each belongs to)."""

    CATCH_AS_CATCH_CAN = "Catch-as-Catch-Can"
    AMOEBOID_ON_A_POLE = "Amoeboid on a Pole"
    IRON_MAN = "Iron Man"
    TRIPLE_THREAT = "Triple Threat"
    MEGA_CHALLENGE_BATTLE_ROYAL = "Mega Challenge: Battle Royal"

    LAST_ONE_PICKED_FOR_DODGEBALL = "Last One Picked For Dodgeball"
    STEEL_IS_STEEL = "Steel Is Steel"
    PUMPING_IRON_MOLTEN_IRON = "Pumping Iron. Molten Iron."
    GREAT_BALLS_OF_FIRE = "Great Balls Of Fire!"
    MEGA_CHALLENGE_PRISON_YARD = "Mega Challenge: Prison Yard"

    NAILS_FOR_BREAKFAST = "Nails for Breakfast"
    TYHRRANOID_RECYCLING = "Tyhrranoid Recycling"
    ITS_RAINING_PHLEGM_HALLELUJAH = "It's Raining Phlegm! Hallelujah!"
    MEATLOAF_TUESDAYS = "Meatloaf Tuesdays"
    MEGA_CHALLENGE_CAFETERIA = "Mega Challenge: Cafeteria"

    NO_GOOD_DEED_GOES_UNPUNISHED = "No good deed goes unpunished."
    COVER_YOUR_SHAME = "Cover Your Shame!"
    DIDNT_NEED_TO_SEE_THAT = "Didn't need to see that!"
    ITS_A_DRY_HEAT = "It's a Dry Heat"
    MEGA_CHALLENGE_SHOWER = "Mega Challenge: Shower"

    KARMIC_BREAKDOWN = "Karmic Breakdown"
    NO_SHELTER = "No Shelter"
    PAST_DUE = "Past Due"
    SPEAK_SOFTLY_AND = "Speak Softly And.."
    MEGA_CHALLENGE_CELLBLOCK = "Mega Challenge: Cellblock"


_CATEGORY = "Ratchet Challenge"

RATCHET_CHALLENGES: tuple[CaseStructure, ...] = (
    CaseStructure(
        SACCases.PRISON_BREAKOUT, SACRatchetChallenges.CATCH_AS_CATCH_CAN, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C54,
    ),
    CaseStructure(
        SACCases.PRISON_BREAKOUT, SACRatchetChallenges.AMOEBOID_ON_A_POLE, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C55,
    ),
    CaseStructure(
        SACCases.PRISON_BREAKOUT, SACRatchetChallenges.IRON_MAN, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C56,
    ),
    CaseStructure(
        SACCases.PRISON_BREAKOUT, SACRatchetChallenges.TRIPLE_THREAT, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C57,
    ),
    CaseStructure(
        SACCases.PRISON_BREAKOUT, SACRatchetChallenges.MEGA_CHALLENGE_BATTLE_ROYAL, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C58,
    ),

    CaseStructure(
        SACCases.THE_EXERCISE_YARD, SACRatchetChallenges.LAST_ONE_PICKED_FOR_DODGEBALL, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C44,
    ),
    CaseStructure(
        SACCases.THE_EXERCISE_YARD, SACRatchetChallenges.STEEL_IS_STEEL, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C45,
    ),
    CaseStructure(
        SACCases.THE_EXERCISE_YARD, SACRatchetChallenges.PUMPING_IRON_MOLTEN_IRON, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C46,
    ),
    CaseStructure(
        SACCases.THE_EXERCISE_YARD, SACRatchetChallenges.GREAT_BALLS_OF_FIRE, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C47,
    ),
    CaseStructure(
        SACCases.THE_EXERCISE_YARD, SACRatchetChallenges.MEGA_CHALLENGE_PRISON_YARD, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C48,
    ),

    CaseStructure(
        SACCases.THE_MESS_HALL, SACRatchetChallenges.NAILS_FOR_BREAKFAST, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C3C,
    ),
    CaseStructure(
        SACCases.THE_MESS_HALL, SACRatchetChallenges.TYHRRANOID_RECYCLING, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C3D,
    ),
    CaseStructure(
        SACCases.THE_MESS_HALL, SACRatchetChallenges.ITS_RAINING_PHLEGM_HALLELUJAH, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C3E,
    ),
    CaseStructure(
        SACCases.THE_MESS_HALL, SACRatchetChallenges.MEATLOAF_TUESDAYS, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C3F,
    ),
    CaseStructure(
        SACCases.THE_MESS_HALL, SACRatchetChallenges.MEGA_CHALLENGE_CAFETERIA, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C40,
    ),

    CaseStructure(
        SACCases.THE_SHOWERS, SACRatchetChallenges.NO_GOOD_DEED_GOES_UNPUNISHED, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C4C,
    ),
    CaseStructure(
        SACCases.THE_SHOWERS, SACRatchetChallenges.COVER_YOUR_SHAME, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C4D,
    ),
    CaseStructure(
        SACCases.THE_SHOWERS, SACRatchetChallenges.DIDNT_NEED_TO_SEE_THAT, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C4E,
    ),
    CaseStructure(
        SACCases.THE_SHOWERS, SACRatchetChallenges.ITS_A_DRY_HEAT, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C4F,
    ),
    CaseStructure(
        SACCases.THE_SHOWERS, SACRatchetChallenges.MEGA_CHALLENGE_SHOWER, _CATEGORY,
        event_flag=0b00000001, event_address=0x206C50,
    ),

    CaseStructure(SACCases.MAX_SECURITY_CELLS, SACRatchetChallenges.KARMIC_BREAKDOWN, _CATEGORY),
    CaseStructure(SACCases.MAX_SECURITY_CELLS, SACRatchetChallenges.NO_SHELTER, _CATEGORY),
    CaseStructure(SACCases.MAX_SECURITY_CELLS, SACRatchetChallenges.PAST_DUE, _CATEGORY),
    CaseStructure(SACCases.MAX_SECURITY_CELLS, SACRatchetChallenges.SPEAK_SOFTLY_AND, _CATEGORY),
    CaseStructure(SACCases.MAX_SECURITY_CELLS, SACRatchetChallenges.MEGA_CHALLENGE_CELLBLOCK, _CATEGORY),
)

# Case.name -> its known Ratchet Challenges' full display names, derived
# from RATCHET_CHALLENGES above. Order is declaration order (display/
# iteration order) and matches native challenge indices within each case.
RATCHET_CHALLENGES_BY_CASE: dict[str, tuple[str, ...]] = group_by_case(RATCHET_CHALLENGES)


@dataclass(frozen=True)
class SACRatchetChallengeLocations:
    """One named constant per Ratchet Challenge location -- each value is the exact full display name RATCHET_CHALLENGES above builds via CaseStructure.__str__, spelled out here so rules/<case>.py can reference an individual location directly -- same one-name-per-location layout as constants/weapons.py's SACRatchetWeapons."""

    PRISON_BREAKOUT_CATCH_AS_CATCH_CAN = "Prison Planet (Ratchet) - Prison Breakout!: Catch-as-Catch-Can"
    PRISON_BREAKOUT_AMOEBOID_ON_A_POLE = "Prison Planet (Ratchet) -  Prison Breakout!: Amoeboid on a Pole"
    PRISON_BREAKOUT_IRON_MAN = "Prison Planet (Ratchet) -  Prison Breakout!: Iron Man"
    PRISON_BREAKOUT_TRIPLE_THREAT = "Prison Planet (Ratchet) -  Prison Breakout!: Triple Threat"
    PRISON_BREAKOUT_MEGA_CHALLENGE_BATTLE_ROYAL = "Prison Planet (Ratchet) -  Prison Breakout!: Mega Challenge: Battle Royal"
    THE_EXERCISE_YARD_LAST_ONE_PICKED_FOR_DODGEBALL = "Prison Planet (Ratchet) - The Exercise Yard: Last One Picked For Dodgeball"
    THE_EXERCISE_YARD_STEEL_IS_STEEL = "Prison Planet (Ratchet) - The Exercise Yard: Steel Is Steel"
    THE_EXERCISE_YARD_PUMPING_IRON_MOLTEN_IRON = "Prison Planet (Ratchet) - The Exercise Yard: Pumping Iron. Molten Iron."
    THE_EXERCISE_YARD_GREAT_BALLS_OF_FIRE = "Prison Planet (Ratchet) - The Exercise Yard: Great Balls Of Fire!"
    THE_EXERCISE_YARD_MEGA_CHALLENGE_PRISON_YARD = "Prison Planet (Ratchet) - The Exercise Yard: Mega Challenge: Prison Yard"
    THE_MESS_HALL_NAILS_FOR_BREAKFAST = "Prison Planet (Ratchet) - The Mess Hall: Nails for Breakfast"
    THE_MESS_HALL_TYHRRANOID_RECYCLING = "Prison Planet (Ratchet) - The Mess Hall: Tyhrranoid Recycling"
    THE_MESS_HALL_ITS_RAINING_PHLEGM_HALLELUJAH = "Prison Planet (Ratchet) - The Mess Hall: It's Raining Phlegm! Hallelujah!"
    THE_MESS_HALL_MEATLOAF_TUESDAYS = "Prison Planet (Ratchet) - The Mess Hall: Meatloaf Tuesdays"
    THE_MESS_HALL_MEGA_CHALLENGE_CAFETERIA = "Prison Planet (Ratchet) - The Mess Hall: Mega Challenge: Cafeteria"
    THE_SHOWERS_NO_GOOD_DEED_GOES_UNPUNISHED = "Prison Planet (Ratchet) - The Showers: No good deed goes unpunished."
    THE_SHOWERS_COVER_YOUR_SHAME = "Prison Planet (Ratchet) - The Showers: Cover Your Shame!"
    THE_SHOWERS_DIDNT_NEED_TO_SEE_THAT = "Prison Planet (Ratchet) - The Showers: Didn't need to see that!"
    THE_SHOWERS_ITS_A_DRY_HEAT = "Prison Planet (Ratchet) - The Showers: It's a Dry Heat"
    THE_SHOWERS_MEGA_CHALLENGE_SHOWER = "Prison Planet (Ratchet) - The Showers: Mega Challenge: Shower"
    MAX_SECURITY_CELLS_KARMIC_BREAKDOWN = "Prison Planet (Ratchet) - Max-Security Cells: Karmic Beatdown"
    MAX_SECURITY_CELLS_NO_SHELTER = "Prison Planet (Ratchet) - Max-Security Cells: No Shelter"
    MAX_SECURITY_CELLS_PAST_DUE = "Prison Planet (Ratchet) - Max-Security Cells: Past Due"
    MAX_SECURITY_CELLS_SPEAK_SOFTLY_AND = "Prison Planet (Ratchet) - Max-Security Cells: Speak Softly And..."
    MAX_SECURITY_CELLS_MEGA_CHALLENGE_CELLBLOCK = "Prison Planet (Ratchet) - Max-Security Cells: Mega Challenge: Cellblock"

assert {v for k, v in vars(SACRatchetChallengeLocations).items() if not k.startswith("_")} == set(
    str(entry) for entry in RATCHET_CHALLENGES
), "SACRatchetChallengeLocations drifted out of sync with RATCHET_CHALLENGES -- regenerate its literals"

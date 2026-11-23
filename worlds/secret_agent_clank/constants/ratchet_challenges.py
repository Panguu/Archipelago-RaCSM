"""Win counters are resolved at runtime from the native arena table, which lists
each case's five challenges consecutively in the order given here.
"""
from dataclasses import dataclass

from .planets import SACCases


@dataclass(frozen=True)
class SACRatchetChallengeLocations:
    PRISON_BREAKOUT_CATCH_AS_CATCH_CAN = "Prison Planet (Ratchet) - Prison Breakout!: Catch-as-Catch-Can"
    PRISON_BREAKOUT_AMOEBOID_ON_A_POLE = "Prison Planet (Ratchet) - Prison Breakout!: Amoeboid on a Pole"
    PRISON_BREAKOUT_IRON_MAN = "Prison Planet (Ratchet) - Prison Breakout!: Iron Man"
    PRISON_BREAKOUT_TRIPLE_THREAT = "Prison Planet (Ratchet) - Prison Breakout!: Triple Threat"
    PRISON_BREAKOUT_MEGA_CHALLENGE_BATTLE_ROYAL = "Prison Planet (Ratchet) - Prison Breakout!: Mega Challenge: Battle Royal"
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


RATCHET_CHALLENGES_BY_CASE: dict[str, tuple[str, ...]] = {
    SACCases.PRISON_BREAKOUT: (
        SACRatchetChallengeLocations.PRISON_BREAKOUT_CATCH_AS_CATCH_CAN,
        SACRatchetChallengeLocations.PRISON_BREAKOUT_AMOEBOID_ON_A_POLE,
        SACRatchetChallengeLocations.PRISON_BREAKOUT_IRON_MAN,
        SACRatchetChallengeLocations.PRISON_BREAKOUT_TRIPLE_THREAT,
        SACRatchetChallengeLocations.PRISON_BREAKOUT_MEGA_CHALLENGE_BATTLE_ROYAL,
    ),
    SACCases.THE_EXERCISE_YARD: (
        SACRatchetChallengeLocations.THE_EXERCISE_YARD_LAST_ONE_PICKED_FOR_DODGEBALL,
        SACRatchetChallengeLocations.THE_EXERCISE_YARD_STEEL_IS_STEEL,
        SACRatchetChallengeLocations.THE_EXERCISE_YARD_PUMPING_IRON_MOLTEN_IRON,
        SACRatchetChallengeLocations.THE_EXERCISE_YARD_GREAT_BALLS_OF_FIRE,
        SACRatchetChallengeLocations.THE_EXERCISE_YARD_MEGA_CHALLENGE_PRISON_YARD,
    ),
    SACCases.THE_MESS_HALL: (
        SACRatchetChallengeLocations.THE_MESS_HALL_NAILS_FOR_BREAKFAST,
        SACRatchetChallengeLocations.THE_MESS_HALL_TYHRRANOID_RECYCLING,
        SACRatchetChallengeLocations.THE_MESS_HALL_ITS_RAINING_PHLEGM_HALLELUJAH,
        SACRatchetChallengeLocations.THE_MESS_HALL_MEATLOAF_TUESDAYS,
        SACRatchetChallengeLocations.THE_MESS_HALL_MEGA_CHALLENGE_CAFETERIA,
    ),
    SACCases.THE_SHOWERS: (
        SACRatchetChallengeLocations.THE_SHOWERS_NO_GOOD_DEED_GOES_UNPUNISHED,
        SACRatchetChallengeLocations.THE_SHOWERS_COVER_YOUR_SHAME,
        SACRatchetChallengeLocations.THE_SHOWERS_DIDNT_NEED_TO_SEE_THAT,
        SACRatchetChallengeLocations.THE_SHOWERS_ITS_A_DRY_HEAT,
        SACRatchetChallengeLocations.THE_SHOWERS_MEGA_CHALLENGE_SHOWER,
    ),
    SACCases.MAX_SECURITY_CELLS: (
        SACRatchetChallengeLocations.MAX_SECURITY_CELLS_KARMIC_BREAKDOWN,
        SACRatchetChallengeLocations.MAX_SECURITY_CELLS_NO_SHELTER,
        SACRatchetChallengeLocations.MAX_SECURITY_CELLS_PAST_DUE,
        SACRatchetChallengeLocations.MAX_SECURITY_CELLS_SPEAK_SOFTLY_AND,
        SACRatchetChallengeLocations.MAX_SECURITY_CELLS_MEGA_CHALLENGE_CELLBLOCK,
    ),
}

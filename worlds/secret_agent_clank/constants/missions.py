"""Story missions per case, and the "<case> Complete" locations used when Missions is level_completion."""
from dataclasses import dataclass
from enum import IntFlag
from typing import NamedTuple

from .planets import SACCases


class MissionFlag(IntFlag):
    DISABLED = 0x0
    ENABLED = 0x1
    UNLOCKED = 0x2
    UNLOCKED_COMPLETED = 0x3


@dataclass(frozen=True)
class SACMissionLocations:
    BOLTAIRE_MUSEUM_ESCAPE_THE_RAVINE = "Boltaire (Clank) - Boltaire Museum: Escape The Ravine Mission"
    BOLTAIRE_MUSEUM_GET_INSIDE_THE_MUSEUM = "Boltaire (Clank) - Boltaire Museum: Get Inside the Museum Mission"
    BOLTAIRE_MUSEUM_NOT_THE_GUIDED_TOUR = "Boltaire (Clank) - Boltaire Museum: Not The Guided Tour Mission"
    BOLTAIRE_GEM_WING_THE_NIGHT_FOX = "Boltaire (Special Missions) - Boltaire Gem Wing: The Night Fox Mission"
    MAX_SECURITY_CELLS_LIFE_IN_PRISON = "Prison Planet (Ratchet) - Max-Security Cells: Life in Prison Mission"
    MAX_SECURITY_CELLS_CONSECUTIVE_LIFE_SENTENCES = "Prison Planet (Ratchet) - Max-Security Cells: Consecutive Life Sentences Mission"
    ROOFTOP_DEATHTRAP_GET_A_CLUE = "Asyanica (Gadgetbots) - Rooftop Deathtrap: Get a Clue Mission"
    ROOFTOP_DEATHTRAP_FREE_AGENT_CLANK = "Asyanica (Gadgetbots) - Rooftop Deathtrap: Free Agent Clank! Mission"
    ROOFTOP_DEATHTRAP_THE_HALLS_OF_ASYANICA = "Asyanica (Gadgetbots) - Rooftop Deathtrap: The Halls of Asyanica Mission"
    ASYANICA_ROOFTOPS_NUMBER_WOO_WORKS_FOR = "Asyanica (Clank) - Asyanica Rooftops: Number Woo works for ... Mission"
    LARGER_THAN_LIFE_QWARKOGRAPHY_CH_1 = "Asyanica (Qwark) - Larger Than Life: Qwarkography, Ch. 1 Mission"
    COUNTESS_VILLA_TANGO_OF_100_SORROWS = "Glaciara (Special Missions) - Countess's Villa: Tango of 100 Sorrows Mission"
    GLACIARA_SKI_SLOPES_BLACK_DIAMOND_OF_DOOM = "Glaciara (Special Missions) - Glaciara, Ski Slopes: Black Diamond of Doom! Mission"
    GLACIARA_SKI_SLOPES_PRO_BOARDING = "Glaciara (Special Missions) - Glaciara, Ski Slopes: Pro Boarding Mission"
    THE_MESS_HALL_NO_TIME_FOR_SECONDS = "Prison Planet (Ratchet) - The Mess Hall: No Time for Seconds Mission"
    THE_MESS_HALL_THE_LUNCH_MENU_FOREVER = "Prison Planet (Ratchet) - The Mess Hall: The Lunch Menu Forever Mission"
    AZCOTAL_ALLEY_THE_KINGPIN = "Rionosis (Clank) - Azcotal Alley: The Kingpin Mission"
    AZCOTAL_ALLEY_ALL_THE_KINGPIN_S_MEN = "Rionosis (Clank) - Azcotal Alley: All the Kingpin's Men Mission"
    GONDOLA_ASCENT_GET_A_LIFT = "Rionosis (Clank) - Gondola Ascent: Get a Lift Mission"
    SUCK_AND_JIVE_QWARKOGRAPHY_THE_GAMBLIN_YEARS = "Rionosis (Qwark) - Suck and Jive: Qwarkography, The Gamblin' Years Mission"
    HIGH_ROLLERS_CASINO_EXPLORE_PARADISE = "The Paradis Des Tricheurs Casino (Clank) - High-Rollers Casino: Explore Paradise Mission"
    HIGH_ROLLERS_CASINO_PARADISE_EXPLOITED = "The Paradis Des Tricheurs Casino (Clank) - High-Rollers Casino: Paradise Exploited Mission"
    THE_EXERCISE_YARD_AND_THE_PASSWORD_IS = "Prison Planet (Ratchet) - The Exercise Yard: And the Password is ... Mission"
    THE_EXERCISE_YARD_FIGHT_FOR_SLIM = "Prison Planet (Ratchet) - The Exercise Yard: Fight for Slim Mission"
    HIGH_STAKES_ROOM_HIGH_RISK_VS_HIGH_STAKES = "The Paradis Des Tricheurs Casino (Special Missions) - High Stakes Room: High Risk vs. High Stakes Mission"
    VENANTONIO_LABS_CRASHING_THE_PARTY = "Venantonio (Clank) - Venantonio Labs: Crashing the Party Mission"
    VENANTONIO_LABS_OUT_OF_THE_FRYING_PAN = "Venantonio (Clank) - Venantonio Labs: Out of the Frying Pan Mission"
    VENANTONIO_CANALS_DANGER_OFF_STARBOARD = "Venantonio (Special Missions) - Venantonio Canals: Danger off Starboard! Mission"
    VENANTONIO_CANALS_POWER_JET_BOATING = "Venantonio (Special Missions) - Venantonio Canals: Power Jet Boating Mission"
    MADAM_BUTTERQWARK_QWARKOGRAPHY_CH_3 = "Venantonio (Qwark) - Madam Butterqwark: Qwarkography, Ch. 3 Mission"
    GALACTIC_BOLT_RESERVE_HARD_CURRENCY = "Fort Sprocket (Clank) - Galactic Bolt Reserve: Hard Currency Mission"
    GALACTIC_BOLT_RESERVE_THE_BIG_HEIST = "Fort Sprocket (Clank) - Galactic Bolt Reserve: The Big Heist Mission"
    INSIDE_THE_A_EYE_PAYBACK_S_A_PUNCH = "Fort Sprocket (Gadgetbots) - Inside the A-Eye: Payback's a Punch Mission"
    INSIDE_THE_A_EYE_MYE_MYNDE_IS_GOING = "Fort Sprocket (Gadgetbots) - Inside the A-Eye: Mye Mynde is Going... Mission"
    THE_SHOWERS_PLUMBING_TROUBLES = "Prison Planet (Ratchet) - The Showers: Plumbing Troubles Mission"
    THE_SHOWERS_RUB_A_DUB_DEATH = "Prison Planet (Ratchet) - The Showers: Rub-a-Dub Death Mission"
    SPACESHIP_GRAVEYARD_TRACKING_THE_KINGPIN = "Spaceship Graveyard (Clank) - Spaceship Graveyard: Tracking the Kingpin Mission"
    SAINT_QWARK_QWARKOGRAPHY_CH_4 = "Spaceship Graveyard (Qwark) - Saint Qwark: Qwarkography, Ch. 4 Mission"
    THE_QUASAR_FIELDS_ESCAPE_THE_KUDZU = "Spaceship Graveyard (Special Missions) - The Quasar Fields: Escape the Kudzu Mission"
    PRISON_BREAKOUT_THE_GREAT_ESCAPE = "Prison Planet (Ratchet) - Prison Breakout!: The Great Escape Mission"
    PRISON_BREAKOUT_AND_NOW_JUSTICE_FOR_ALL = "Prison Planet (Ratchet) - Prison Breakout!: And Now... Justice for All Mission"
    DAMS_EDGE_HYDRANO_SHIP_S_SIGNAL = "Hydrano (Special Missions) - Dam's Edge, Hydrano: Ship's Signal Mission"
    DAMS_EDGE_HYDRANO_FOLLOW_THAT_CAR = "Hydrano (Special Missions) - Dam's Edge, Hydrano: Follow That Car Mission"
    DAMS_EDGE_HYDRANO_THE_DRIFT_KING = "Hydrano (Special Missions) - Dam's Edge, Hydrano: The Drift King Mission"
    A_FICTION_FULL_OF_DOLLARS_QWARKOGRAPHY_CH_5 = "Hydrano (Qwark) - A Fiction Full Of Dollars: Qwarkography, Ch. 5 Mission"
    BULKHEAD_LOCK_UNDERWATER_BASE = "Hydrano (Gadgetbots) - Bulkhead Lock: Underwater Base Mission"
    BULKHEAD_LOCK_LOCKED_DOOR = "Hydrano (Gadgetbots) - Bulkhead Lock: Locked Door Mission"
    BULKHEAD_LOCK_INSULT_TO_INJURY = "Hydrano (Gadgetbots) - Bulkhead Lock: Insult to Injury Mission"
    UNDERWATER_BUNKER_CLANK_UNDER_GLASS = "Hydrano (Clank) - Underwater Bunker: Clank Under Glass Mission"
    KLUNKS_LAIR_ALL_THE_MARBLES = "Hydrano (Clank) - Klunk's Lair: All the Marbles Mission"
    HIGH_TREEHOUSE_HIGH_IMPACT_TREEHOUSE = "High Impact Treehouse (Special Missions) - High Impact Treehouse: High Impact Treehouse Mission"
    BOLTAIRE_MUSEUM_COMPLETE = "Boltaire (Clank) - Boltaire Museum: Boltaire Museum Complete"
    BOLTAIRE_GEM_WING_COMPLETE = "Boltaire (Special Missions) - Boltaire Gem Wing: Boltaire Gem Wing Complete"
    MAX_SECURITY_CELLS_COMPLETE = "Prison Planet (Ratchet) - Max-Security Cells: Max-Security Cells Complete"
    ROOFTOP_DEATHTRAP_COMPLETE = "Asyanica (Gadgetbots) - Rooftop Deathtrap: Rooftop Deathtrap Complete"
    ASYANICA_ROOFTOPS_COMPLETE = "Asyanica (Clank) - Asyanica Rooftops: Asyanica Rooftops Complete"
    LARGER_THAN_LIFE_COMPLETE = "Asyanica (Qwark) - Larger Than Life: Larger Than Life Complete"
    COUNTESS_VILLA_COMPLETE = "Glaciara (Special Missions) - Countess's Villa: Countess's Villa Complete"
    GLACIARA_SKI_SLOPES_COMPLETE = "Glaciara (Special Missions) - Glaciara, Ski Slopes: Glaciara, Ski Slopes Complete"
    THE_MESS_HALL_COMPLETE = "Prison Planet (Ratchet) - The Mess Hall: The Mess Hall Complete"
    AZCOTAL_ALLEY_COMPLETE = "Rionosis (Clank) - Azcotal Alley: Azcotal Alley Complete"
    GONDOLA_ASCENT_COMPLETE = "Rionosis (Clank) - Gondola Ascent: Gondola Ascent Complete"
    SUCK_AND_JIVE_COMPLETE = "Rionosis (Qwark) - Suck and Jive: Suck and Jive Complete"
    HIGH_ROLLERS_CASINO_COMPLETE = "The Paradis Des Tricheurs Casino (Clank) - High-Rollers Casino: High-Rollers Casino Complete"
    THE_EXERCISE_YARD_COMPLETE = "Prison Planet (Ratchet) - The Exercise Yard: The Exercise Yard Complete"
    HIGH_STAKES_ROOM_COMPLETE = "The Paradis Des Tricheurs Casino (Special Missions) - High Stakes Room: High Stakes Room Complete"
    VENANTONIO_LABS_COMPLETE = "Venantonio (Clank) - Venantonio Labs: Venantonio Labs Complete"
    VENANTONIO_CANALS_COMPLETE = "Venantonio (Special Missions) - Venantonio Canals: Venantonio Canals Complete"
    MADAM_BUTTERQWARK_COMPLETE = "Venantonio (Qwark) - Madam Butterqwark: Madam Butterqwark Complete"
    GALACTIC_BOLT_RESERVE_COMPLETE = "Fort Sprocket (Clank) - Galactic Bolt Reserve: Galactic Bolt Reserve Complete"
    INSIDE_THE_A_EYE_COMPLETE = "Fort Sprocket (Gadgetbots) - Inside the A-Eye: Inside the A-Eye Complete"
    THE_SHOWERS_COMPLETE = "Prison Planet (Ratchet) - The Showers: The Showers Complete"
    SPACESHIP_GRAVEYARD_COMPLETE = "Spaceship Graveyard (Clank) - Spaceship Graveyard: Spaceship Graveyard Complete"
    SAINT_QWARK_COMPLETE = "Spaceship Graveyard (Qwark) - Saint Qwark: Saint Qwark Complete"
    THE_QUASAR_FIELDS_COMPLETE = "Spaceship Graveyard (Special Missions) - The Quasar Fields: The Quasar Fields Complete"
    PRISON_BREAKOUT_COMPLETE = "Prison Planet (Ratchet) - Prison Breakout!: Prison Breakout! Complete"
    DAMS_EDGE_HYDRANO_COMPLETE = "Hydrano (Special Missions) - Dam's Edge, Hydrano: Dam's Edge, Hydrano Complete"
    A_FICTION_FULL_OF_DOLLARS_COMPLETE = "Hydrano (Qwark) - A Fiction Full Of Dollars: A Fiction Full Of Dollars Complete"
    BULKHEAD_LOCK_COMPLETE = "Hydrano (Gadgetbots) - Bulkhead Lock: Bulkhead Lock Complete"
    UNDERWATER_BUNKER_COMPLETE = "Hydrano (Clank) - Underwater Bunker: Underwater Bunker Complete"
    KLUNKS_LAIR_COMPLETE = "Hydrano (Clank) - Klunk's Lair: Klunk's Lair Complete"
    HIGH_TREEHOUSE_COMPLETE = "High Impact Treehouse (Special Missions) - High Impact Treehouse: High Impact Treehouse Complete"


class SACMissionEntry(NamedTuple):
    name: str      # SACMissionLocations constant
    title_id: int  # native USA mission title ID, used to verify a resolved chapter


# Each case's missions in native task order. Native case labels split shared
# module slots; task addresses are resolved at runtime.
CHAPTER_ENTRIES: dict[str, tuple[SACMissionEntry, ...]] = {
    SACCases.BOLTAIRE_MUSEUM: (
        SACMissionEntry(SACMissionLocations.BOLTAIRE_MUSEUM_ESCAPE_THE_RAVINE, 5501),
        SACMissionEntry(SACMissionLocations.BOLTAIRE_MUSEUM_GET_INSIDE_THE_MUSEUM, 5503),
        SACMissionEntry(SACMissionLocations.BOLTAIRE_MUSEUM_NOT_THE_GUIDED_TOUR, 5505),
    ),
    SACCases.BOLTAIRE_GEM_WING: (
        SACMissionEntry(SACMissionLocations.BOLTAIRE_GEM_WING_THE_NIGHT_FOX, 5507),
    ),
    SACCases.MAX_SECURITY_CELLS: (
        SACMissionEntry(SACMissionLocations.MAX_SECURITY_CELLS_LIFE_IN_PRISON, 5509),
        SACMissionEntry(SACMissionLocations.MAX_SECURITY_CELLS_CONSECUTIVE_LIFE_SENTENCES, 5511),
    ),
    SACCases.ROOFTOP_DEATHTRAP: (
        SACMissionEntry(SACMissionLocations.ROOFTOP_DEATHTRAP_GET_A_CLUE, 5513),
        SACMissionEntry(SACMissionLocations.ROOFTOP_DEATHTRAP_FREE_AGENT_CLANK, 5515),
        SACMissionEntry(SACMissionLocations.ROOFTOP_DEATHTRAP_THE_HALLS_OF_ASYANICA, 5517),
    ),
    SACCases.ASYANICA_ROOFTOPS: (
        SACMissionEntry(SACMissionLocations.ASYANICA_ROOFTOPS_NUMBER_WOO_WORKS_FOR, 5519),
    ),
    SACCases.LARGER_THAN_LIFE: (
        SACMissionEntry(SACMissionLocations.LARGER_THAN_LIFE_QWARKOGRAPHY_CH_1, 5521),
    ),
    SACCases.COUNTESS_VILLA: (
        SACMissionEntry(SACMissionLocations.COUNTESS_VILLA_TANGO_OF_100_SORROWS, 5523),
    ),
    SACCases.GLACIARA_SKI_SLOPES: (
        SACMissionEntry(SACMissionLocations.GLACIARA_SKI_SLOPES_BLACK_DIAMOND_OF_DOOM, 5525),
        SACMissionEntry(SACMissionLocations.GLACIARA_SKI_SLOPES_PRO_BOARDING, 5591),
    ),
    SACCases.THE_MESS_HALL: (
        SACMissionEntry(SACMissionLocations.THE_MESS_HALL_NO_TIME_FOR_SECONDS, 5527),
        SACMissionEntry(SACMissionLocations.THE_MESS_HALL_THE_LUNCH_MENU_FOREVER, 5529),
    ),
    SACCases.AZCOTAL_ALLEY: (
        SACMissionEntry(SACMissionLocations.AZCOTAL_ALLEY_THE_KINGPIN, 5531),
        SACMissionEntry(SACMissionLocations.AZCOTAL_ALLEY_ALL_THE_KINGPIN_S_MEN, 5533),
    ),
    SACCases.GONDOLA_ASCENT: (
        SACMissionEntry(SACMissionLocations.GONDOLA_ASCENT_GET_A_LIFT, 5535),
    ),
    SACCases.SUCK_AND_JIVE: (
        SACMissionEntry(SACMissionLocations.SUCK_AND_JIVE_QWARKOGRAPHY_THE_GAMBLIN_YEARS, 5537),
    ),
    SACCases.HIGH_ROLLERS_CASINO: (
        SACMissionEntry(SACMissionLocations.HIGH_ROLLERS_CASINO_EXPLORE_PARADISE, 5539),
        SACMissionEntry(SACMissionLocations.HIGH_ROLLERS_CASINO_PARADISE_EXPLOITED, 5541),
    ),
    SACCases.THE_EXERCISE_YARD: (
        SACMissionEntry(SACMissionLocations.THE_EXERCISE_YARD_AND_THE_PASSWORD_IS, 5543),
        SACMissionEntry(SACMissionLocations.THE_EXERCISE_YARD_FIGHT_FOR_SLIM, 5545),
    ),
    SACCases.HIGH_STAKES_ROOM: (
        SACMissionEntry(SACMissionLocations.HIGH_STAKES_ROOM_HIGH_RISK_VS_HIGH_STAKES, 5547),
    ),
    SACCases.VENANTONIO_LABS: (
        SACMissionEntry(SACMissionLocations.VENANTONIO_LABS_CRASHING_THE_PARTY, 5549),
        SACMissionEntry(SACMissionLocations.VENANTONIO_LABS_OUT_OF_THE_FRYING_PAN, 5551),
    ),
    SACCases.VENANTONIO_CANALS: (
        SACMissionEntry(SACMissionLocations.VENANTONIO_CANALS_DANGER_OFF_STARBOARD, 5553),
        SACMissionEntry(SACMissionLocations.VENANTONIO_CANALS_POWER_JET_BOATING, 5593),
    ),
    SACCases.MADAM_BUTTERQWARK: (
        SACMissionEntry(SACMissionLocations.MADAM_BUTTERQWARK_QWARKOGRAPHY_CH_3, 5555),
    ),
    SACCases.GALACTIC_BOLT_RESERVE: (
        SACMissionEntry(SACMissionLocations.GALACTIC_BOLT_RESERVE_HARD_CURRENCY, 5557),
        SACMissionEntry(SACMissionLocations.GALACTIC_BOLT_RESERVE_THE_BIG_HEIST, 5559),
    ),
    SACCases.INSIDE_THE_A_EYE: (
        SACMissionEntry(SACMissionLocations.INSIDE_THE_A_EYE_PAYBACK_S_A_PUNCH, 5561),
        SACMissionEntry(SACMissionLocations.INSIDE_THE_A_EYE_MYE_MYNDE_IS_GOING, 5597),
    ),
    SACCases.THE_SHOWERS: (
        SACMissionEntry(SACMissionLocations.THE_SHOWERS_PLUMBING_TROUBLES, 5563),
        SACMissionEntry(SACMissionLocations.THE_SHOWERS_RUB_A_DUB_DEATH, 5565),
    ),
    SACCases.SPACESHIP_GRAVEYARD: (
        SACMissionEntry(SACMissionLocations.SPACESHIP_GRAVEYARD_TRACKING_THE_KINGPIN, 5567),
    ),
    SACCases.SAINT_QWARK: (
        SACMissionEntry(SACMissionLocations.SAINT_QWARK_QWARKOGRAPHY_CH_4, 5569),
    ),
    SACCases.THE_QUASAR_FIELDS: (
        SACMissionEntry(SACMissionLocations.THE_QUASAR_FIELDS_ESCAPE_THE_KUDZU, 5571),
    ),
    SACCases.PRISON_BREAKOUT: (
        SACMissionEntry(SACMissionLocations.PRISON_BREAKOUT_THE_GREAT_ESCAPE, 5573),
        SACMissionEntry(SACMissionLocations.PRISON_BREAKOUT_AND_NOW_JUSTICE_FOR_ALL, 5575),
    ),
    SACCases.DAMS_EDGE_HYDRANO: (
        SACMissionEntry(SACMissionLocations.DAMS_EDGE_HYDRANO_SHIP_S_SIGNAL, 5579),
        SACMissionEntry(SACMissionLocations.DAMS_EDGE_HYDRANO_FOLLOW_THAT_CAR, 5577),
        SACMissionEntry(SACMissionLocations.DAMS_EDGE_HYDRANO_THE_DRIFT_KING, 5595),
    ),
    SACCases.A_FICTION_FULL_OF_DOLLARS: (
        SACMissionEntry(SACMissionLocations.A_FICTION_FULL_OF_DOLLARS_QWARKOGRAPHY_CH_5, 5581),
    ),
    SACCases.BULKHEAD_LOCK: (
        SACMissionEntry(SACMissionLocations.BULKHEAD_LOCK_UNDERWATER_BASE, 5583),
        SACMissionEntry(SACMissionLocations.BULKHEAD_LOCK_LOCKED_DOOR, 5585),
        SACMissionEntry(SACMissionLocations.BULKHEAD_LOCK_INSULT_TO_INJURY, 5599),
    ),
    SACCases.UNDERWATER_BUNKER: (
        SACMissionEntry(SACMissionLocations.UNDERWATER_BUNKER_CLANK_UNDER_GLASS, 5587),
    ),
    SACCases.KLUNKS_LAIR: (
        SACMissionEntry(SACMissionLocations.KLUNKS_LAIR_ALL_THE_MARBLES, 5589),
    ),
    SACCases.HIGH_TREEHOUSE: (
        SACMissionEntry(SACMissionLocations.HIGH_TREEHOUSE_HIGH_IMPACT_TREEHOUSE, 5636),
    ),
}

MISSION_COMPLETE_NAME: dict[str, str] = {
    SACCases.BOLTAIRE_MUSEUM: SACMissionLocations.BOLTAIRE_MUSEUM_COMPLETE,
    SACCases.BOLTAIRE_GEM_WING: SACMissionLocations.BOLTAIRE_GEM_WING_COMPLETE,
    SACCases.MAX_SECURITY_CELLS: SACMissionLocations.MAX_SECURITY_CELLS_COMPLETE,
    SACCases.ROOFTOP_DEATHTRAP: SACMissionLocations.ROOFTOP_DEATHTRAP_COMPLETE,
    SACCases.ASYANICA_ROOFTOPS: SACMissionLocations.ASYANICA_ROOFTOPS_COMPLETE,
    SACCases.LARGER_THAN_LIFE: SACMissionLocations.LARGER_THAN_LIFE_COMPLETE,
    SACCases.COUNTESS_VILLA: SACMissionLocations.COUNTESS_VILLA_COMPLETE,
    SACCases.GLACIARA_SKI_SLOPES: SACMissionLocations.GLACIARA_SKI_SLOPES_COMPLETE,
    SACCases.THE_MESS_HALL: SACMissionLocations.THE_MESS_HALL_COMPLETE,
    SACCases.AZCOTAL_ALLEY: SACMissionLocations.AZCOTAL_ALLEY_COMPLETE,
    SACCases.GONDOLA_ASCENT: SACMissionLocations.GONDOLA_ASCENT_COMPLETE,
    SACCases.SUCK_AND_JIVE: SACMissionLocations.SUCK_AND_JIVE_COMPLETE,
    SACCases.HIGH_ROLLERS_CASINO: SACMissionLocations.HIGH_ROLLERS_CASINO_COMPLETE,
    SACCases.THE_EXERCISE_YARD: SACMissionLocations.THE_EXERCISE_YARD_COMPLETE,
    SACCases.HIGH_STAKES_ROOM: SACMissionLocations.HIGH_STAKES_ROOM_COMPLETE,
    SACCases.VENANTONIO_LABS: SACMissionLocations.VENANTONIO_LABS_COMPLETE,
    SACCases.VENANTONIO_CANALS: SACMissionLocations.VENANTONIO_CANALS_COMPLETE,
    SACCases.MADAM_BUTTERQWARK: SACMissionLocations.MADAM_BUTTERQWARK_COMPLETE,
    SACCases.GALACTIC_BOLT_RESERVE: SACMissionLocations.GALACTIC_BOLT_RESERVE_COMPLETE,
    SACCases.INSIDE_THE_A_EYE: SACMissionLocations.INSIDE_THE_A_EYE_COMPLETE,
    SACCases.THE_SHOWERS: SACMissionLocations.THE_SHOWERS_COMPLETE,
    SACCases.SPACESHIP_GRAVEYARD: SACMissionLocations.SPACESHIP_GRAVEYARD_COMPLETE,
    SACCases.SAINT_QWARK: SACMissionLocations.SAINT_QWARK_COMPLETE,
    SACCases.THE_QUASAR_FIELDS: SACMissionLocations.THE_QUASAR_FIELDS_COMPLETE,
    SACCases.PRISON_BREAKOUT: SACMissionLocations.PRISON_BREAKOUT_COMPLETE,
    SACCases.DAMS_EDGE_HYDRANO: SACMissionLocations.DAMS_EDGE_HYDRANO_COMPLETE,
    SACCases.A_FICTION_FULL_OF_DOLLARS: SACMissionLocations.A_FICTION_FULL_OF_DOLLARS_COMPLETE,
    SACCases.BULKHEAD_LOCK: SACMissionLocations.BULKHEAD_LOCK_COMPLETE,
    SACCases.UNDERWATER_BUNKER: SACMissionLocations.UNDERWATER_BUNKER_COMPLETE,
    SACCases.KLUNKS_LAIR: SACMissionLocations.KLUNKS_LAIR_COMPLETE,
    SACCases.HIGH_TREEHOUSE: SACMissionLocations.HIGH_TREEHOUSE_COMPLETE,
}

MISSION_NAMES: tuple[str, ...] = tuple(entry.name for entries in CHAPTER_ENTRIES.values() for entry in entries)

# These single-mission cases use the next case's intro as their retail finish
# predicate. AP permits out-of-order travel, so capture their actual exit instead.
NATIVE_FINISH_CASES = {
    24: SACCases.THE_QUASAR_FIELDS,
    29: SACCases.UNDERWATER_BUNKER,
}

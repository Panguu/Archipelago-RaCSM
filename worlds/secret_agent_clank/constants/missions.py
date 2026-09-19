"""String constants for story mission names -- the real per-case mission title, as opposed to locations.py's "{case.name} Complete" placeholder used until every mission has a real case/address (see core/missions.py)."""

from dataclasses import dataclass
from enum import IntFlag

from .planets import SACCases


@dataclass(frozen=True)
class SACMissions:
    """String constants for real story mission titles (short form only -- see CHAPTER_ENTRIES below for which case/address/flag each belongs to)."""

    ESCAPE_THE_RAVINE = "Escape The Ravine"
    GET_INSIDE_THE_MUSEUM = "Get Inside the Museum"
    NOT_THE_GUIDED_TOUR = "Not The Guided Tour"
    THE_NIGHT_FOX = "The Night Fox"
    LIFE_IN_PRISON = "Life in Prison"
    GET_A_CLUE = "Get a Clue"
    FREE_AGENT_CLANK = "Free Agent Clank!"
    NUMBER_WOO_WORKS_FOR_ME = "Number Woo works for ..."
    LARGER_THAN_LIFE = "Qwarkography, Ch. 1"
    TANGO_OF_100_SORROWS = "Tango of 100 Sorrows"
    BLACK_DIAMOND_OF_DOOM = "Black Diamond of Doom!"
    NO_TIME_FOR_SECONDS = "No Time for Seconds"
    THE_LUNCH_MENU_FOREVER = "The Lunch Menu Forever"
    THE_KINGPIN = "The Kingpin"
    ALL_THE_KINGPINS_MEN = "All the Kingpin's Men"
    GET_A_LIFT = "Get a Lift"
    SUCK_AND_JIVE = "Qwarkography, The Gamblin' Years"
    EXPLORE_PARADISE = "Explore Paradise"
    PARADISE_EXPLOITED = "Paradise Exploited"
    AND_THE_PASSWORD_IS = "And the Password is ..."
    FIGHT_FOR_SLIM = "Fight for Slim"
    HIGH_RISK_VS_HIGH_STAKES = "High Risk vs. High Stakes"
    CRASHING_THE_PARTY = "Crashing the Party"
    OUT_OF_THE_FRYING_PAN = "Out of the Frying Pan"
    DANGER_OFF_STARBOARD = "Danger off Starboard!"
    MADAM_BUTTERQWARK = "Qwarkography, Ch. 3"
    HARD_CURRENCY = "Hard Currency"
    THE_BIG_HEIST = "The Big Heist"
    PAYBACKS_A_PUNCH = "Payback's a Punch"
    PLUMBING_TROUBLES = "Plumbing Troubles"
    RUB_A_DUB_DEATH = "Rub-a-Dub Death"
    TRACKING_THE_KINGPIN = "Tracking the Kingpin"
    SAINT_QWARK = "Qwarkography, Ch. 4"
    ESCAPE_THE_KUDZU = "Escape the Kudzu"
    THE_GREAT_ESCAPE = "The Great Escape"
    AND_NOW_JUSTICE_FOR_ALL = "And Now... Justice for All"
    SHIPS_SIGNAL = "Ship's Signal"
    FOLLOW_THAT_CAR = "Follow That Car"
    A_FICTION_FULL_OF_DOLLARS = "Qwarkography, Ch. 5"
    UNDERWATER_BASE = "Underwater Base"
    LOCKED_DOOR = "Locked Door"
    CLANK_UNDER_GLASS = "Clank Under Glass"
    ALL_THE_MARBLES = "All the Marbles"
    KLUNKS_LAIR = "Klunk's Lair"
    HIGH_TREEHOUSE = "High Impact Treehouse"

    CONSECUTIVE_LIFE_SENTENCES = "Consecutive Life Sentences"
    THE_HALLS_OF_ASYANICA = "The Halls of Asyanica"
    PRO_BOARDING = "Pro Boarding"
    POWER_JET_BOATING = "Power Jet Boating"
    MYE_MYNDE_IS_GOING = "Mye Mynde is Going..."
    THE_DRIFT_KING = "The Drift King"
    INSULT_TO_INJURY = "Insult to Injury"

class MissionFlag(IntFlag):
    DISABLED = 0x0
    ENABLED = 0x1
    UNLOCKED = 0x2
    UNLOCKED_COMPLETED = 0x3

@dataclass
class SACMissionEntry:
    name: SACMissions
    address: int
    flag: MissionFlag = MissionFlag.DISABLED
    title_id: int = 0

    def __post_init__(self) -> None:
        # A property/setter pair here (instead of this) would collide with
        # the dataclass-generated __init__: the property definition
        # overwrites the field's default value in the class namespace
        # before @dataclass ever reads it, so every no-flag-given
        # construction (i.e. every CHAPTER_ENTRIES entry) would raise
        # instead of defaulting to MissionFlag.DISABLED.
        if not isinstance(self.flag, MissionFlag):
            raise ValueError(f"Expected a MissionFlag, got {type(self.flag)}")


# USA mission titles and title IDs decoded from the native string/mission tables.
# Native case labels split shared module slots. Addresses are resolved at runtime.
CHAPTER_ENTRIES = {
    SACCases.BOLTAIRE_MUSEUM: [
        SACMissionEntry(name=SACMissions.ESCAPE_THE_RAVINE, address=0, title_id=5501),
        SACMissionEntry(name=SACMissions.GET_INSIDE_THE_MUSEUM, address=0, title_id=5503),
        SACMissionEntry(name=SACMissions.NOT_THE_GUIDED_TOUR, address=0, title_id=5505),
    ],
    SACCases.BOLTAIRE_GEM_WING: [
        SACMissionEntry(name=SACMissions.THE_NIGHT_FOX, address=0, title_id=5507),
    ],
    SACCases.MAX_SECURITY_CELLS: [
        SACMissionEntry(name=SACMissions.LIFE_IN_PRISON, address=0, title_id=5509),
        SACMissionEntry(name=SACMissions.CONSECUTIVE_LIFE_SENTENCES, address=0, title_id=5511),
    ],
    SACCases.ROOFTOP_DEATHTRAP: [
        SACMissionEntry(name=SACMissions.GET_A_CLUE, address=0, title_id=5513),
        SACMissionEntry(name=SACMissions.FREE_AGENT_CLANK, address=0, title_id=5515),
        SACMissionEntry(name=SACMissions.THE_HALLS_OF_ASYANICA, address=0, title_id=5517),
    ],
    SACCases.ASYANICA_ROOFTOPS: [
        SACMissionEntry(name=SACMissions.NUMBER_WOO_WORKS_FOR_ME, address=0, title_id=5519),
    ],
    SACCases.LARGER_THAN_LIFE: [
        SACMissionEntry(name=SACMissions.LARGER_THAN_LIFE, address=0, title_id=5521),
    ],
    SACCases.COUNTESS_VILLA: [
        SACMissionEntry(name=SACMissions.TANGO_OF_100_SORROWS, address=0, title_id=5523),
    ],
    SACCases.GLACIARA_SKI_SLOPES: [
        SACMissionEntry(name=SACMissions.BLACK_DIAMOND_OF_DOOM, address=0, title_id=5525),
        SACMissionEntry(name=SACMissions.PRO_BOARDING, address=0, title_id=5591),
    ],
    SACCases.THE_MESS_HALL: [
        SACMissionEntry(name=SACMissions.NO_TIME_FOR_SECONDS, address=0, title_id=5527),
        SACMissionEntry(name=SACMissions.THE_LUNCH_MENU_FOREVER, address=0, title_id=5529),
    ],
    SACCases.AZCOTAL_ALLEY: [
        SACMissionEntry(name=SACMissions.THE_KINGPIN, address=0, title_id=5531),
        SACMissionEntry(name=SACMissions.ALL_THE_KINGPINS_MEN, address=0, title_id=5533),
    ],
    SACCases.GONDOLA_ASCENT: [
        SACMissionEntry(name=SACMissions.GET_A_LIFT, address=0, title_id=5535),
    ],
    SACCases.SUCK_AND_JIVE: [
        SACMissionEntry(name=SACMissions.SUCK_AND_JIVE, address=0, title_id=5537),
    ],
    SACCases.HIGH_ROLLERS_CASINO: [
        SACMissionEntry(name=SACMissions.EXPLORE_PARADISE, address=0, title_id=5539),
        SACMissionEntry(name=SACMissions.PARADISE_EXPLOITED, address=0, title_id=5541),
    ],
    SACCases.THE_EXERCISE_YARD: [
        SACMissionEntry(name=SACMissions.AND_THE_PASSWORD_IS, address=0, title_id=5543),
        SACMissionEntry(name=SACMissions.FIGHT_FOR_SLIM, address=0, title_id=5545),
    ],
    SACCases.HIGH_STAKES_ROOM: [
        SACMissionEntry(name=SACMissions.HIGH_RISK_VS_HIGH_STAKES, address=0, title_id=5547),
    ],
    SACCases.VENANTONIO_LABS: [
        SACMissionEntry(name=SACMissions.CRASHING_THE_PARTY, address=0, title_id=5549),
        SACMissionEntry(name=SACMissions.OUT_OF_THE_FRYING_PAN, address=0, title_id=5551),
    ],
    SACCases.VENANTONIO_CANALS: [
        SACMissionEntry(name=SACMissions.DANGER_OFF_STARBOARD, address=0, title_id=5553),
        SACMissionEntry(name=SACMissions.POWER_JET_BOATING, address=0, title_id=5593),
    ],
    SACCases.MADAM_BUTTERQWARK: [
        SACMissionEntry(name=SACMissions.MADAM_BUTTERQWARK, address=0, title_id=5555),
    ],
    SACCases.GALACTIC_BOLT_RESERVE: [
        SACMissionEntry(name=SACMissions.HARD_CURRENCY, address=0, title_id=5557),
        SACMissionEntry(name=SACMissions.THE_BIG_HEIST, address=0, title_id=5559),
    ],
    SACCases.INSIDE_THE_A_EYE: [
        SACMissionEntry(name=SACMissions.PAYBACKS_A_PUNCH, address=0, title_id=5561),
        SACMissionEntry(name=SACMissions.MYE_MYNDE_IS_GOING, address=0, title_id=5597),
    ],
    SACCases.THE_SHOWERS: [
        SACMissionEntry(name=SACMissions.PLUMBING_TROUBLES, address=0, title_id=5563),
        SACMissionEntry(name=SACMissions.RUB_A_DUB_DEATH, address=0, title_id=5565),
    ],
    SACCases.SPACESHIP_GRAVEYARD: [
        SACMissionEntry(name=SACMissions.TRACKING_THE_KINGPIN, address=0, title_id=5567),
    ],
    SACCases.SAINT_QWARK: [
        SACMissionEntry(name=SACMissions.SAINT_QWARK, address=0, title_id=5569),
    ],
    SACCases.THE_QUASAR_FIELDS: [
        SACMissionEntry(name=SACMissions.ESCAPE_THE_KUDZU, address=0, title_id=5571),
    ],
    SACCases.PRISON_BREAKOUT: [
        SACMissionEntry(name=SACMissions.THE_GREAT_ESCAPE, address=0, title_id=5573),
        SACMissionEntry(name=SACMissions.AND_NOW_JUSTICE_FOR_ALL, address=0, title_id=5575),
    ],
    SACCases.DAMS_EDGE_HYDRANO: [
        SACMissionEntry(name=SACMissions.SHIPS_SIGNAL, address=0, title_id=5579),
        SACMissionEntry(name=SACMissions.FOLLOW_THAT_CAR, address=0, title_id=5577),
        SACMissionEntry(name=SACMissions.THE_DRIFT_KING, address=0, title_id=5595),
    ],
    SACCases.A_FICTION_FULL_OF_DOLLARS: [
        SACMissionEntry(name=SACMissions.A_FICTION_FULL_OF_DOLLARS, address=0, title_id=5581),
    ],
    SACCases.BULKHEAD_LOCK: [
        SACMissionEntry(name=SACMissions.UNDERWATER_BASE, address=0, title_id=5583),
        SACMissionEntry(name=SACMissions.LOCKED_DOOR, address=0, title_id=5585),
        SACMissionEntry(name=SACMissions.INSULT_TO_INJURY, address=0, title_id=5599),
    ],
    SACCases.UNDERWATER_BUNKER: [
        SACMissionEntry(name=SACMissions.CLANK_UNDER_GLASS, address=0, title_id=5587),
    ],
    SACCases.KLUNKS_LAIR: [
        SACMissionEntry(name=SACMissions.ALL_THE_MARBLES, address=0, title_id=5589),
    ],
    SACCases.HIGH_TREEHOUSE: [
        SACMissionEntry(name=SACMissions.HIGH_TREEHOUSE, address=0, title_id=5636),
    ],
}

# Flat (case_name, SACMissionEntry) pairs from CHAPTER_ENTRIES, in
# declaration order -- for core/missions.py's MissionInventory and client
# debug commands that need to walk every mission regardless of case.
ALL_CHAPTER_ENTRIES: tuple[tuple[str, SACMissionEntry], ...] = tuple(
    (case_name, entry) for case_name, entries in CHAPTER_ENTRIES.items() for entry in entries
)

MISSION_TO_CASE: dict[str, str] = {entry.name: case_name for case_name, entry in ALL_CHAPTER_ENTRIES}

# Mission full name -> its SACMissionEntry (address + flag), for O(1)
# lookup by name -- e.g. client debug commands that write a single
# mission's flag byte directly rather than walking the whole table.
MISSION_NAME_TO_CHAPTER_ENTRY: dict[str, SACMissionEntry] = {
    entry.name: entry for _, entry in ALL_CHAPTER_ENTRIES
}


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
    PRISON_BREAKOUT_THE_GREAT_ESCAPE = "Prison Planet (Ratchet) -  Prison Breakout!: The Great Escape Mission"
    PRISON_BREAKOUT_AND_NOW_JUSTICE_FOR_ALL = "Prison Planet (Ratchet) -  Prison Breakout!: And Now... Justice for All Mission"
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
    PRISON_BREAKOUT_COMPLETE = "Prison Planet (Ratchet) -  Prison Breakout!: Prison Breakout! Complete"
    DAMS_EDGE_HYDRANO_COMPLETE = "Hydrano (Special Missions) - Dam's Edge, Hydrano: Dam's Edge, Hydrano Complete"
    A_FICTION_FULL_OF_DOLLARS_COMPLETE = "Hydrano (Qwark) - A Fiction Full Of Dollars: A Fiction Full Of Dollars Complete"
    BULKHEAD_LOCK_COMPLETE = "Hydrano (Gadgetbots) - Bulkhead Lock: Bulkhead Lock Complete"
    UNDERWATER_BUNKER_COMPLETE = "Hydrano (Clank) - Underwater Bunker: Underwater Bunker Complete"
    KLUNKS_LAIR_COMPLETE = "Hydrano (Clank) - Klunk's Lair: Klunk's Lair Complete"
    HIGH_TREEHOUSE_COMPLETE = "High Impact Treehouse (Special Missions) - High Impact Treehouse: High Impact Treehouse Complete"

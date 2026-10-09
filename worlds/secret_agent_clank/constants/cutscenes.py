"""Cutscene locations, enabled by the All Cutscenes option."""
from dataclasses import dataclass

from .types import EventFlag


@dataclass(frozen=True)
class SACCutsceneLocations:
    BOLTAIRE_MUSEUM_ENTER_CUTSCENE = "Boltaire (Clank) - Boltaire Museum: Enter Cutscene"
    BOLTAIRE_GEM_WING_COMPLETE_CASE_CUTSCENE = "Boltaire (Special Missions) - Boltaire Gem Wing: Complete Case Cutscene"
    MAX_SECURITY_CELLS_ENTER_CUTSCENE = "Prison Planet (Ratchet) - Max-Security Cells: Enter Cutscene"
    ROOFTOP_DEATHTRAP_ENTER_CUTSCENE = "Asyanica (Gadgetbots) - Rooftop Deathtrap: Enter Cutscene"
    ROOFTOP_DEATHTRAP_RESCURE_CLANK_CUTSCENE = "Asyanica (Gadgetbots) - Rooftop Deathtrap: Rescure Clank Cutscene"
    LARGER_THAN_LIFE_ENTER_CUTSCENE = "Asyanica (Qwark) - Larger Than Life: Enter Cutscene"
    LARGER_THAN_LIFE_GODZILLA_LAZER_BEAM = "Asyanica (Qwark) - Larger Than Life: Godzilla Lazer Beam"
    LARGER_THAN_LIFE_COMPLETE_CUTSCENE = "Asyanica (Qwark) - Larger Than Life: Complete Cutscene"
    COUNTESS_VILLA_ENTER_THE_MANSION = "Glaciara (Special Missions) - Countess's Villa: Enter the mansion"
    COUNTESS_VILLA_COMPLETE_DANCE_CUTSCENE = "Glaciara (Special Missions) - Countess's Villa: Complete Dance Cutscene"
    THE_MESS_HALL_ENTER_CUTSCENE = "Prison Planet (Ratchet) - The Mess Hall: Enter Cutscene"
    AZCOTAL_ALLEY_ENTER_CUTSCENE = "Rionosis (Clank) - Azcotal Alley: Enter Cutscene"
    AZCOTAL_ALLEY_MEET_JACK_CUTSCENE = "Rionosis (Clank) - Azcotal Alley: Meet Jack Cutscene"
    GONDOLA_ASCENT_FINISH_GONDOLA_CUTSCENE = "Rionosis (Clank) - Gondola Ascent: Finish Gondola Cutscene"
    SUCK_AND_JIVE_DEFEAT_JACK_CUTSCENE = "Rionosis (Qwark) - Suck and Jive: Defeat Jack Cutscene"
    HIGH_ROLLERS_CASINO_ENTER_CUTSCENE = "The Paradis Des Tricheurs Casino (Clank) - High-Rollers Casino: Enter Cutscene"
    HIGH_ROLLERS_CASINO_COMPLETE_CUTSCENE = "The Paradis Des Tricheurs Casino (Clank) - High-Rollers Casino: Complete Cutscene"
    THE_EXERCISE_YARD_COMPLETE_CUTSCENE = "Prison Planet (Ratchet) - The Exercise Yard: Complete Cutscene"
    VENANTONIO_LABS_ENTER_CUTSCENE = "Venantonio (Clank) - Venantonio Labs: Enter Cutscene"
    VENANTONIO_LABS_OPEN_GREEN_DOOR_CUTSCENE = "Venantonio (Clank) - Venantonio Labs: Open Green Door Cutscene"
    VENANTONIO_LABS_COMPLETE_CUTSCENE = "Venantonio (Clank) - Venantonio Labs: Complete Cutscene"
    VENANTONIO_CANALS_COMPLETE_CUTSCENE = "Venantonio (Special Missions) - Venantonio Canals: Complete Cutscene"
    MADAM_BUTTERQWARK_ENTER_CUTSCENE = "Venantonio (Qwark) - Madam Butterqwark: Enter Cutscene"
    MADAM_BUTTERQWARK_COMPLETE_CUTSCENE = "Venantonio (Qwark) - Madam Butterqwark: Complete Cutscene"
    GALACTIC_BOLT_RESERVE_ENTER_CUTSCENE = "Fort Sprocket (Clank) - Galactic Bolt Reserve: Enter Cutscene"
    GALACTIC_BOLT_RESERVE_COMPLETE_CUTSCENE = "Fort Sprocket (Clank) - Galactic Bolt Reserve: Complete Cutscene"
    INSIDE_THE_A_EYE_COMPLETE_CUTSCENE = "Fort Sprocket (Gadgetbots) - Inside the A-Eye: Complete Cutscene"
    THE_SHOWERS_ENTER_CUTSCENE = "Prison Planet (Ratchet) - The Showers: Enter Cutscene"
    SPACESHIP_GRAVEYARD_COMPLETE_CUTSCENE = "Spaceship Graveyard (Clank) - Spaceship Graveyard: Complete Cutscene"
    SAINT_QWARK_ENTERE_CUTSCENE = "Spaceship Graveyard (Qwark) - Saint Qwark: Enter Cutscene"
    PRISON_BREAKOUT_ENTER_CUTSCENE = "Prison Planet (Ratchet) - Prison Breakout!: Enter Cutscene"
    DAMS_EDGE_HYDRANO_ENTER_CUTSCENE = "Hydrano (Special Missions) - Dam's Edge, Hydrano: Enter Cutscene"
    DAMS_EDGE_HYDRANO_COMPLETE_CUTSCENE = "Hydrano (Special Missions) - Dam's Edge, Hydrano: Complete Cutscene"
    A_FICTION_FULL_OF_DOLLARS_ENTER_CUTSCENE = "Hydrano (Qwark) - A Fiction Full Of Dollars: Enter Cutscene"
    A_FICTION_FULL_OF_DOLLARS_COMPLETE_CUTSCENE = "Hydrano (Qwark) - A Fiction Full Of Dollars: Complete Cutscene"
    BULKHEAD_LOCK_ENTER_CUTSCENE = "Hydrano (Gadgetbots) - Bulkhead Lock: Enter Cutscene"
    KLUNKS_LAIR_ENTERE_CUTSCENE = "Hydrano (Clank) - Klunk's Lair: Enter Cutscene"
    KLUNKS_LAIR_MID_FIGHT_CUTSCENE_FOR_ROBO_RATCHET = "Hydrano (Clank) - Klunk's Lair: Mid Fight Cutscene for Robo Ratchet"
    KLUNKS_LAIR_COMPLETE_CUTSCENE = "Hydrano (Clank) - Klunk's Lair: Complete Cutscene"
    KLUNKS_LAIR_HIGH_IMPACT_GAMES_CUTSCENE_WITH_GIANT_CLANK = "Hydrano (Clank) - Klunk's Lair: High Impact Games Cutscene with Giant Clank"


# Every cutscene's flag lives in the shared 0x206BE0-0x206BF4 bitmask region.
CUTSCENE_FLAGS: dict[str, EventFlag] = {
    SACCutsceneLocations.BOLTAIRE_MUSEUM_ENTER_CUTSCENE: EventFlag(0x206BE0, 0b00000001),
    SACCutsceneLocations.BOLTAIRE_GEM_WING_COMPLETE_CASE_CUTSCENE: EventFlag(0x206BE0, 0b00000100),
    SACCutsceneLocations.MAX_SECURITY_CELLS_ENTER_CUTSCENE: EventFlag(0x206BE0, 0b00001000),
    SACCutsceneLocations.ROOFTOP_DEATHTRAP_ENTER_CUTSCENE: EventFlag(0x206BE2, 0b00000001),
    SACCutsceneLocations.ROOFTOP_DEATHTRAP_RESCURE_CLANK_CUTSCENE: EventFlag(0x206BE2, 0b00000010),
    SACCutsceneLocations.LARGER_THAN_LIFE_ENTER_CUTSCENE: EventFlag(0x206BE2, 0b00001000),
    SACCutsceneLocations.LARGER_THAN_LIFE_GODZILLA_LAZER_BEAM: EventFlag(0x206BE2, 0b00100000),
    SACCutsceneLocations.LARGER_THAN_LIFE_COMPLETE_CUTSCENE: EventFlag(0x206BE2, 0b00010000),
    SACCutsceneLocations.COUNTESS_VILLA_ENTER_THE_MANSION: EventFlag(0x206BE4, 0b00000001),
    SACCutsceneLocations.COUNTESS_VILLA_COMPLETE_DANCE_CUTSCENE: EventFlag(0x206BE4, 0b00000010),
    SACCutsceneLocations.THE_MESS_HALL_ENTER_CUTSCENE: EventFlag(0x206BE4, 0b00000100),
    SACCutsceneLocations.AZCOTAL_ALLEY_ENTER_CUTSCENE: EventFlag(0x206BE6, 0b00000001),
    SACCutsceneLocations.AZCOTAL_ALLEY_MEET_JACK_CUTSCENE: EventFlag(0x206BE6, 0b00000010),
    SACCutsceneLocations.GONDOLA_ASCENT_FINISH_GONDOLA_CUTSCENE: EventFlag(0x206BE6, 0b00000100),
    SACCutsceneLocations.SUCK_AND_JIVE_DEFEAT_JACK_CUTSCENE: EventFlag(0x206BE6, 0b00010000),
    SACCutsceneLocations.HIGH_ROLLERS_CASINO_ENTER_CUTSCENE: EventFlag(0x206BE8, 0b00000001),
    SACCutsceneLocations.HIGH_ROLLERS_CASINO_COMPLETE_CUTSCENE: EventFlag(0x206BE8, 0b00000010),
    SACCutsceneLocations.THE_EXERCISE_YARD_COMPLETE_CUTSCENE: EventFlag(0x206BE8, 0b00000100),
    SACCutsceneLocations.VENANTONIO_LABS_ENTER_CUTSCENE: EventFlag(0x206BEA, 0b00000001),
    SACCutsceneLocations.VENANTONIO_LABS_OPEN_GREEN_DOOR_CUTSCENE: EventFlag(0x206BEA, 0b00000010),
    SACCutsceneLocations.VENANTONIO_LABS_COMPLETE_CUTSCENE: EventFlag(0x206BEA, 0b00000100),
    SACCutsceneLocations.VENANTONIO_CANALS_COMPLETE_CUTSCENE: EventFlag(0x206BEA, 0b00001000),
    SACCutsceneLocations.MADAM_BUTTERQWARK_ENTER_CUTSCENE: EventFlag(0x206BEA, 0b00010000),
    SACCutsceneLocations.MADAM_BUTTERQWARK_COMPLETE_CUTSCENE: EventFlag(0x206BEA, 0b00100000),
    SACCutsceneLocations.GALACTIC_BOLT_RESERVE_ENTER_CUTSCENE: EventFlag(0x206BEC, 0b00000001),
    SACCutsceneLocations.GALACTIC_BOLT_RESERVE_COMPLETE_CUTSCENE: EventFlag(0x206BEC, 0b00000010),
    SACCutsceneLocations.INSIDE_THE_A_EYE_COMPLETE_CUTSCENE: EventFlag(0x206BEC, 0b00000100),
    SACCutsceneLocations.THE_SHOWERS_ENTER_CUTSCENE: EventFlag(0x206BEC, 0b00001000),
    SACCutsceneLocations.SPACESHIP_GRAVEYARD_COMPLETE_CUTSCENE: EventFlag(0x206BEE, 0b00000010),
    SACCutsceneLocations.SAINT_QWARK_ENTERE_CUTSCENE: EventFlag(0x206BEE, 0b00000100),
    SACCutsceneLocations.PRISON_BREAKOUT_ENTER_CUTSCENE: EventFlag(0x206BF0, 0b00000001),
    SACCutsceneLocations.DAMS_EDGE_HYDRANO_ENTER_CUTSCENE: EventFlag(0x206BF0, 0b00000010),
    SACCutsceneLocations.DAMS_EDGE_HYDRANO_COMPLETE_CUTSCENE: EventFlag(0x206BF0, 0b00000100),
    SACCutsceneLocations.A_FICTION_FULL_OF_DOLLARS_ENTER_CUTSCENE: EventFlag(0x206BF0, 0b00001000),
    SACCutsceneLocations.A_FICTION_FULL_OF_DOLLARS_COMPLETE_CUTSCENE: EventFlag(0x206BF0, 0b00010000),
    SACCutsceneLocations.BULKHEAD_LOCK_ENTER_CUTSCENE: EventFlag(0x206BF2, 0b00000001),
    SACCutsceneLocations.KLUNKS_LAIR_ENTERE_CUTSCENE: EventFlag(0x206BF2, 0b00000010),
    SACCutsceneLocations.KLUNKS_LAIR_MID_FIGHT_CUTSCENE_FOR_ROBO_RATCHET: EventFlag(0x206BF2, 0b00000100),
    SACCutsceneLocations.KLUNKS_LAIR_COMPLETE_CUTSCENE: EventFlag(0x206BF2, 0b00001000),
    SACCutsceneLocations.KLUNKS_LAIR_HIGH_IMPACT_GAMES_CUTSCENE_WITH_GIANT_CLANK: EventFlag(0x206BF4, 0b00001100),
}

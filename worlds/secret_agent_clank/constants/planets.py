from dataclasses import dataclass

from .operatives import SACOperatives
from .types import Case


@dataclass(frozen=True)
class SACPlanets:
    BOLTAIRE_MUSEUM = "Boltaire Museum"
    PRISON_PLANET = "Prison Planet"
    ASYANICA = "Asyanica"
    GLACIARA = "Glaciara"
    RIONOSIS = "Rionosis"
    CASINO = "Le Paradis Des Tricheurs Casino"
    VENANTONIO = "Venantonio"
    FORT_SPROCKET = "Fort Sprocket"
    SPACESHIP_GRAVEYARD = "Spaceship Graveyard"
    HYDRANO = "Hydrano"


@dataclass(frozen=True)
class SACCases:
    BOLTAIRE_MUSEUM = "Case File (Clank): Boltaire Museum"
    BOLTAIRE_GEM_WING = "Case File (Special Missions): Boltaire Gem Wing"
    MAX_SECURITY_CELLS = "Case File (Ratchet): Max-Security Cells"
    ROOFTOP_DEATHTRAP = "Case File (Gadgetbots): Rooftop Deathtrap"
    ASYANICA_ROOFTOPS = "Case File (Clank): Asyanica Rooftops"
    LARGER_THAN_LIFE = "Case File (Qwark): Larger Than Life"
    COUNTESS_VILLA = "Case File (Special Missions): Countess's Villa"
    GLACIARA_SKI_SLOPES = "Case File (Special Missions): Glaciara, Ski Slopes"
    THE_MESS_HALL = "Case File (Ratchet): The Mess Hall"
    AZCOTAL_ALLEY = "Case File (Clank): Azcotal Alley"
    GONDOLA_ASCENT = "Case File (Clank): Gondola Ascent"
    SUCK_AND_JIVE = "Case File (Qwark): Suck and Jive"
    HIGH_ROLLERS_CASINO = "Case File (Clank): High-Rollers Casino"
    THE_EXERCISE_YARD = "Case File (Ratchet): The Exercise Yard"
    HIGH_STAKES_ROOM = "Case File (Special Missions): High Stakes Room"
    VENANTONIO_LABS = "Case File (Clank): Venantonio Labs"
    VENANTONIO_CANALS = "Case File (Special Missions): Venantonio Canals"
    MADAM_BUTTERQWARK = "Case File (Qwark): Madam Butterqwark"
    GALACTIC_BOLT_RESERVE = "Case File (Clank): Galactic Bolt Reserve"
    INSIDE_THE_A_EYE = "Case File (Gadgetbots): Inside the A-Eye"
    THE_SHOWERS = "Case File (Ratchet): The Showers"
    SPACESHIP_GRAVEYARD = "Case File (Clank): Spaceship Graveyard"
    SAINT_QWARK = "Case File (Qwark): Saint Qwark"
    THE_QUASAR_FIELDS = "Case File (Special Missions): The Quasar Fields"
    PRISON_BREAKOUT = "Case File (Ratchet): Prison Breakout!"
    DAMS_EDGE_HYDRANO = "Case File (Special Missions): Dam's Edge, Hydrano"
    A_FICTION_FULL_OF_DOLLARS = "Case File (Qwark): A Fiction Full Of Dollars"
    BULKHEAD_LOCK = "Case File (Gadgetbots): Bulkhead Lock"
    UNDERWATER_BUNKER = "Case File (Clank): Underwater Bunker"
    KLUNKS_LAIR = "Case File (Clank): Klunk's Lair"
    HIGH_TREEHOUSE = "Case File (Special Missions): High Impact Treehouse"


ALL_CASES: tuple[Case, ...] = (
    Case(SACCases.BOLTAIRE_MUSEUM, 1, SACPlanets.BOLTAIRE_MUSEUM, SACOperatives.CLANK),
    Case(SACCases.BOLTAIRE_GEM_WING, 2, SACPlanets.BOLTAIRE_MUSEUM, SACOperatives.SPECIAL_MISSIONS),
    Case(SACCases.MAX_SECURITY_CELLS, 3, SACPlanets.PRISON_PLANET, SACOperatives.RATCHET),
    Case(SACCases.ROOFTOP_DEATHTRAP, 4, SACPlanets.ASYANICA, SACOperatives.GADGETBOTS),
    Case(SACCases.LARGER_THAN_LIFE, 5, SACPlanets.ASYANICA, SACOperatives.QWARK, menu_id=8),
    Case(SACCases.COUNTESS_VILLA, 6, SACPlanets.GLACIARA, SACOperatives.SPECIAL_MISSIONS),
    Case(SACCases.ASYANICA_ROOFTOPS, 7, SACPlanets.ASYANICA, SACOperatives.CLANK),
    Case(SACCases.GLACIARA_SKI_SLOPES, 8, SACPlanets.GLACIARA, SACOperatives.SPECIAL_MISSIONS, menu_id=10),
    Case(SACCases.THE_MESS_HALL, 9, SACPlanets.PRISON_PLANET, SACOperatives.RATCHET, menu_id=12),
    Case(SACCases.AZCOTAL_ALLEY, 10, SACPlanets.RIONOSIS, SACOperatives.CLANK),
    Case(SACCases.GONDOLA_ASCENT, 11, SACPlanets.RIONOSIS, SACOperatives.CLANK),
    Case(SACCases.SUCK_AND_JIVE, 12, SACPlanets.RIONOSIS, SACOperatives.QWARK),
    Case(SACCases.HIGH_ROLLERS_CASINO, 13, SACPlanets.CASINO, SACOperatives.CLANK),
    Case(SACCases.THE_EXERCISE_YARD, 14, SACPlanets.PRISON_PLANET, SACOperatives.RATCHET),
    Case(SACCases.HIGH_STAKES_ROOM, 15, SACPlanets.CASINO, SACOperatives.SPECIAL_MISSIONS),
    Case(SACCases.VENANTONIO_LABS, 16, SACPlanets.VENANTONIO, SACOperatives.CLANK),
    Case(SACCases.VENANTONIO_CANALS, 17, SACPlanets.VENANTONIO, SACOperatives.SPECIAL_MISSIONS),
    Case(SACCases.MADAM_BUTTERQWARK, 18, SACPlanets.VENANTONIO, SACOperatives.QWARK),
    Case(SACCases.GALACTIC_BOLT_RESERVE, 19, SACPlanets.FORT_SPROCKET, SACOperatives.CLANK),
    Case(SACCases.INSIDE_THE_A_EYE, 20, SACPlanets.FORT_SPROCKET, SACOperatives.GADGETBOTS),
    Case(SACCases.THE_SHOWERS, 21, SACPlanets.PRISON_PLANET, SACOperatives.RATCHET),
    Case(SACCases.SPACESHIP_GRAVEYARD, 22, SACPlanets.SPACESHIP_GRAVEYARD, SACOperatives.CLANK),
    Case(SACCases.SAINT_QWARK, 23, SACPlanets.SPACESHIP_GRAVEYARD, SACOperatives.QWARK),
    Case(SACCases.THE_QUASAR_FIELDS, 24, SACPlanets.SPACESHIP_GRAVEYARD, SACOperatives.SPECIAL_MISSIONS),
    Case(SACCases.PRISON_BREAKOUT, 25, SACPlanets.PRISON_PLANET, SACOperatives.RATCHET),
    Case(SACCases.DAMS_EDGE_HYDRANO, 26, SACPlanets.HYDRANO, SACOperatives.SPECIAL_MISSIONS),
    Case(SACCases.A_FICTION_FULL_OF_DOLLARS, 27, SACPlanets.HYDRANO, SACOperatives.QWARK),
    Case(SACCases.BULKHEAD_LOCK, 28, SACPlanets.HYDRANO, SACOperatives.GADGETBOTS),
    Case(SACCases.UNDERWATER_BUNKER, 29, SACPlanets.HYDRANO, SACOperatives.CLANK),
    Case(SACCases.KLUNKS_LAIR, 30, SACPlanets.HYDRANO, SACOperatives.CLANK),
)

PLANET_NAMES: tuple[str, ...] = tuple(dict.fromkeys(case.planet for case in ALL_CASES))
OPERATIVE_NAMES: tuple[str, ...] = tuple(dict.fromkeys(case.operative for case in ALL_CASES))

CASE_ID_TO_CASE: dict[int, Case] = {case.case_id: case for case in ALL_CASES}
CASE_NAME_TO_CASE: dict[str, Case] = {case.name: case for case in ALL_CASES}
CASE_NAME_TO_PLANET: dict[str, str] = {case.name: case.planet for case in ALL_CASES}
CASE_NAME_TO_OPERATIVE: dict[str, str] = {case.name: case.operative for case in ALL_CASES}

CASES_BY_PLANET: dict[str, tuple[Case, ...]] = {
    planet: tuple(case for case in ALL_CASES if case.planet == planet) for planet in PLANET_NAMES
}
CASES_BY_OPERATIVE: dict[str, tuple[Case, ...]] = {
    operative: tuple(case for case in ALL_CASES if case.operative == operative) for operative in OPERATIVE_NAMES
}

PROGRESSIVE_PLANET_ITEM_NAME: dict[str, str] = {
    planet: f"Progressive {planet}" for planet in PLANET_NAMES
}

CASE_NAME_TO_INFOBOT: dict[str, str] = {
    case.name: case.name for case in ALL_CASES
}

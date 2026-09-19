from dataclasses import dataclass

from .operatives import SACOperatives
from .types import Case


@dataclass(frozen=True)
class SACPlanets:
    """String constants for each planet."""

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
    """String constants for each case."""

    BOLTAIRE_MUSEUM = "Case File: Boltaire Museum"
    BOLTAIRE_GEM_WING = "Case File: Boltaire Gem Wing"
    MAX_SECURITY_CELLS = "Case File: Max-Security Cells"
    ROOFTOP_DEATHTRAP = "Case File: Rooftop Deathtrap"
    ASYANICA_ROOFTOPS = "Case File: Asyanica Rooftops"
    LARGER_THAN_LIFE = "Case File: Larger Than Life"
    COUNTESS_VILLA = "Case File: Countess's Villa"
    GLACIARA_SKI_SLOPES = "Case File: Glaciara, Ski Slopes"
    THE_MESS_HALL = "Case File: The Mess Hall"
    AZCOTAL_ALLEY = "Case File: Azcotal Alley"
    GONDOLA_ASCENT = "Case File: Gondola Ascent"
    SUCK_AND_JIVE = "Case File: Suck and Jive"
    HIGH_ROLLERS_CASINO = "Case File: High-Rollers Casino"
    THE_EXERCISE_YARD = "Case File: The Exercise Yard"
    HIGH_STAKES_ROOM = "Case File: High Stakes Room"
    VENANTONIO_LABS = "Case File: Venantonio Labs"
    VENANTONIO_CANALS = "Case File: Venantonio Canals"
    MADAM_BUTTERQWARK = "Case File: Madam Butterqwark"
    GALACTIC_BOLT_RESERVE = "Case File: Galactic Bolt Reserve"
    INSIDE_THE_A_EYE = "Case File: Inside the A-Eye"
    THE_SHOWERS = "Case File: The Showers"
    SPACESHIP_GRAVEYARD = "Case File: Spaceship Graveyard"
    SAINT_QWARK = "Case File: Saint Qwark"
    THE_QUASAR_FIELDS = "Case File: The Quasar Fields"
    PRISON_BREAKOUT = "Case File: Prison Breakout!"
    DAMS_EDGE_HYDRANO = "Case File: Dam's Edge, Hydrano"
    A_FICTION_FULL_OF_DOLLARS = "Case File: A Fiction Full Of Dollars"
    BULKHEAD_LOCK = "Case File: Bulkhead Lock"
    UNDERWATER_BUNKER = "Case File: Underwater Bunker"
    KLUNKS_LAIR = "Case File: Klunk's Lair"
    HIGH_TREEHOUSE = "Case File: High Impact Treehouse"


ALL_CASES: tuple[Case, ...] = (
    Case(SACCases.BOLTAIRE_MUSEUM, 1, SACPlanets.BOLTAIRE_MUSEUM, SACOperatives.CLANK),
    Case(SACCases.BOLTAIRE_GEM_WING, 2, SACPlanets.BOLTAIRE_MUSEUM, SACOperatives.SPECIAL_MISSIONS),
    Case(SACCases.MAX_SECURITY_CELLS, 3, SACPlanets.PRISON_PLANET, SACOperatives.RATCHET),
    # planet still LOW CONFIDENCE — escape sequence, guessed prison rather than Asyanica
    Case(SACCases.ROOFTOP_DEATHTRAP, 4, SACPlanets.ASYANICA, SACOperatives.GADGETBOTS),
    Case(SACCases.LARGER_THAN_LIFE, 5, SACPlanets.ASYANICA, SACOperatives.QWARK, menu_id=8),
    Case(SACCases.COUNTESS_VILLA, 6, SACPlanets.GLACIARA, SACOperatives.SPECIAL_MISSIONS),
    Case(SACCases.ASYANICA_ROOFTOPS, 7, SACPlanets.ASYANICA, SACOperatives.CLANK),
    Case(SACCases.GLACIARA_SKI_SLOPES, 8, SACPlanets.GLACIARA, SACOperatives.SPECIAL_MISSIONS, menu_id=10),
    Case(SACCases.THE_MESS_HALL, 9, SACPlanets.PRISON_PLANET, SACOperatives.RATCHET, menu_id=12),
    # planet LOW CONFIDENCE
    Case(SACCases.AZCOTAL_ALLEY, 10, SACPlanets.GLACIARA, SACOperatives.CLANK),
    # planet LOW CONFIDENCE — assumed ski-lift, not Venantonio's canal gondolas
    Case(SACCases.GONDOLA_ASCENT, 11, SACPlanets.GLACIARA, SACOperatives.CLANK),
    # planet LOW CONFIDENCE — only leftover planet, no name clue tying it here
    Case(SACCases.SUCK_AND_JIVE, 12, SACPlanets.RIONOSIS, SACOperatives.QWARK),
    Case(SACCases.HIGH_ROLLERS_CASINO, 13, SACPlanets.CASINO, SACOperatives.CLANK),
    Case(SACCases.THE_EXERCISE_YARD, 14, SACPlanets.PRISON_PLANET, SACOperatives.RATCHET),
    Case(SACCases.HIGH_STAKES_ROOM, 15, SACPlanets.CASINO, SACOperatives.SPECIAL_MISSIONS),
    Case(SACCases.VENANTONIO_LABS, 16, SACPlanets.VENANTONIO, SACOperatives.CLANK),
    Case(SACCases.VENANTONIO_CANALS, 17, SACPlanets.VENANTONIO, SACOperatives.SPECIAL_MISSIONS),
    # planet LOW CONFIDENCE; operative LOW CONFIDENCE — inferred from "Qwarkography Ch. 3" flavor text
    Case(SACCases.MADAM_BUTTERQWARK, 18, SACPlanets.VENANTONIO, SACOperatives.QWARK),
    # planet LOW CONFIDENCE; operative LOW CONFIDENCE — inferred from disguise/stealth flavor text
    Case(SACCases.GALACTIC_BOLT_RESERVE, 19, SACPlanets.VENANTONIO, SACOperatives.CLANK),
    # planet LOW CONFIDENCE
    Case(SACCases.INSIDE_THE_A_EYE, 20, SACPlanets.FORT_SPROCKET, SACOperatives.GADGETBOTS),
    # planet LOW CONFIDENCE
    Case(SACCases.THE_SHOWERS, 21, SACPlanets.PRISON_PLANET, SACOperatives.RATCHET),
    # operative LOW CONFIDENCE — inferred from Holo-Monocle stealth flavor text
    Case(SACCases.SPACESHIP_GRAVEYARD, 22, SACPlanets.SPACESHIP_GRAVEYARD, SACOperatives.CLANK),
    # operative LOW CONFIDENCE — inferred from "Qwarkography Ch. 4" flavor text (name itself is a strong clue too)
    Case(SACCases.SAINT_QWARK, 23, SACPlanets.SPACESHIP_GRAVEYARD, SACOperatives.QWARK),
    # operative LOW CONFIDENCE — inferred from space-combat/vehicle flavor text
    Case(SACCases.THE_QUASAR_FIELDS, 24, SACPlanets.SPACESHIP_GRAVEYARD, SACOperatives.SPECIAL_MISSIONS),
    Case(SACCases.PRISON_BREAKOUT, 25, SACPlanets.PRISON_PLANET, SACOperatives.RATCHET),
    Case(SACCases.DAMS_EDGE_HYDRANO, 26, SACPlanets.HYDRANO, SACOperatives.SPECIAL_MISSIONS),
    # planet LOW CONFIDENCE; operative LOW CONFIDENCE — inferred from "Qwarkography Ch. 5" flavor text
    Case(SACCases.A_FICTION_FULL_OF_DOLLARS, 27, SACPlanets.HYDRANO, SACOperatives.QWARK),
    # planet LOW CONFIDENCE
    Case(SACCases.BULKHEAD_LOCK, 28, SACPlanets.FORT_SPROCKET, SACOperatives.GADGETBOTS),
    # operative LOW CONFIDENCE — inferred from Blackout Pen/Holo-Monocle (Clank gadgets) flavor text
    Case(SACCases.UNDERWATER_BUNKER, 29, SACPlanets.HYDRANO, SACOperatives.CLANK),
    # operative LOW CONFIDENCE — inferred from stealth-takedown-on-Klunk flavor text
    Case(SACCases.KLUNKS_LAIR, 30, SACPlanets.HYDRANO, SACOperatives.CLANK),
)

# Fixed display/iteration order -- first appearance in ALL_CASES.
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

# Display name -> the AP item that grants access to that planet's cases.
# One access item per planet, mirroring the infobot-per-planet pattern the
# other RaC worlds use — see items.py's PLANET_ACCESS_ITEM_TABLE. The
# starting planet (Boltaire Museum) has none -- it's always reachable, see
# rules.py.
PLANET_ACCESS_ITEM_NAME: dict[str, str] = {
    planet: f"{planet} Access" for planet in PLANET_NAMES[1:]
}

# Case.name -> the Case File item that grants access to that specific
# case -- SAC's own in-game term for these (not "Infobot", which is the
# other RaC worlds' naming). Finer-grained than PLANET_ACCESS_ITEM_NAME
# above -- used by rules.py to gate individual per-case locations (e.g.
# skill points, see locations.py's SKILL_POINT_LOCATION_TO_CASE) on top of
# the coarser planet-entrance gate. Includes the starting case (case_id 1,
# Boltaire Museum) too -- world.py's create_items() precollects its Case
# File unconditionally rather than special-casing it as "always true" in
# the rules, so it's a real starting-inventory item like any other.
CASE_NAME_TO_INFOBOT: dict[str, str] = {
    case.name: case.name for case in ALL_CASES
}

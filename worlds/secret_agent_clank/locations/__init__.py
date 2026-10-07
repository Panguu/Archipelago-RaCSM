"""Gathers each case file's region and the other location records, and builds per-category lookups."""
from .a_fiction_full_of_dollars import REGION as A_FICTION_FULL_OF_DOLLARS
from .asyanica_rooftops import REGION as ASYANICA_ROOFTOPS
from .azcotal_alley import REGION as AZCOTAL_ALLEY
from .boltaire_gem_wing import REGION as BOLTAIRE_GEM_WING
from .boltaire_museum import REGION as BOLTAIRE_MUSEUM
from .bulkhead_lock import REGION as BULKHEAD_LOCK
from .countess_villa import REGION as COUNTESS_VILLA
from .dams_edge_hydrano import REGION as DAMS_EDGE_HYDRANO
from .galactic_bolt_reserve import REGION as GALACTIC_BOLT_RESERVE
from .glaciara_ski_slopes import REGION as GLACIARA_SKI_SLOPES
from .gondola_ascent import REGION as GONDOLA_ASCENT
from .high_rollers_casino import REGION as HIGH_ROLLERS_CASINO
from .high_stakes_room import REGION as HIGH_STAKES_ROOM
from .inside_the_a_eye import REGION as INSIDE_THE_A_EYE
from .klunks_lair import REGION as KLUNKS_LAIR
from .larger_than_life import REGION as LARGER_THAN_LIFE
from .madam_butterqwark import REGION as MADAM_BUTTERQWARK
from .max_security_cells import REGION as MAX_SECURITY_CELLS
from .model import BASE_ID, CaseRegion, SACLocation, SACLocationType
from .nanotech import NANOTECH_LOCATIONS, RATCHET_NANOTECH_LOCATIONS
from .prison_breakout import REGION as PRISON_BREAKOUT
from .rooftop_deathtrap import REGION as ROOFTOP_DEATHTRAP
from .saint_qwark import REGION as SAINT_QWARK
from .spaceship_graveyard import REGION as SPACESHIP_GRAVEYARD
from .stealth import STEALTH_TAKEDOWN_LOCATIONS
from .suck_and_jive import REGION as SUCK_AND_JIVE
from .the_exercise_yard import REGION as THE_EXERCISE_YARD
from .the_mess_hall import REGION as THE_MESS_HALL
from .the_quasar_fields import REGION as THE_QUASAR_FIELDS
from .the_showers import REGION as THE_SHOWERS
from .underwater_bunker import REGION as UNDERWATER_BUNKER
from .venantonio_canals import REGION as VENANTONIO_CANALS
from .venantonio_labs import REGION as VENANTONIO_LABS
from . import vendors
from .weapon_levels import WEAPON_LEVEL_LOCATIONS

__all__ = [
    "ALIEN_CODE_LOCATIONS",
    "ALL_LOCATIONS",
    "BASE_ID",
    "BASE_VENDOR_LOCATIONS",
    "CASE_LOCATIONS",
    "CASE_REGIONS",
    "KEYCARD_LOCATIONS",
    "LOCATIONS",
    "LOCATION_NAME_TO_ID",
    "MOD_VENDOR_LOCATIONS",
    "RATCHET_CHALLENGE_LOCATIONS",
    "SKILL_POINT_LOCATIONS",
    "TITANIUM_BOLT_LOCATIONS",
    "TITAN_VENDOR_LOCATIONS",
    "CaseRegion",
    "SACLocation",
    "SACLocationType",
]

# Case name -> its region. Regions are created in ALL_CASES order; this order only fixes location listing order.
CASE_REGIONS: dict[str, CaseRegion] = {
    region.case: region for region in (
        BOLTAIRE_MUSEUM,
        BOLTAIRE_GEM_WING,
        MAX_SECURITY_CELLS,
        ROOFTOP_DEATHTRAP,
        ASYANICA_ROOFTOPS,
        LARGER_THAN_LIFE,
        COUNTESS_VILLA,
        GLACIARA_SKI_SLOPES,
        THE_MESS_HALL,
        AZCOTAL_ALLEY,
        GONDOLA_ASCENT,
        SUCK_AND_JIVE,
        HIGH_ROLLERS_CASINO,
        THE_EXERCISE_YARD,
        HIGH_STAKES_ROOM,
        VENANTONIO_LABS,
        VENANTONIO_CANALS,
        MADAM_BUTTERQWARK,
        GALACTIC_BOLT_RESERVE,
        INSIDE_THE_A_EYE,
        THE_SHOWERS,
        SPACESHIP_GRAVEYARD,
        SAINT_QWARK,
        THE_QUASAR_FIELDS,
        PRISON_BREAKOUT,
        DAMS_EDGE_HYDRANO,
        A_FICTION_FULL_OF_DOLLARS,
        BULKHEAD_LOCK,
        UNDERWATER_BUNKER,
        KLUNKS_LAIR,
    )
}
CASE_LOCATIONS: tuple[SACLocation, ...] = tuple(
    location for region in CASE_REGIONS.values() for location in region.locations
)
LOCATIONS: tuple[SACLocation, ...] = (
    *CASE_LOCATIONS,
    *vendors.BASE_VENDOR_LOCATIONS,
    *vendors.TITAN_VENDOR_LOCATIONS,
    *vendors.MOD_VENDOR_LOCATIONS,
    *WEAPON_LEVEL_LOCATIONS.values(),
    *NANOTECH_LOCATIONS.values(),
    *STEALTH_TAKEDOWN_LOCATIONS.values(),
    *RATCHET_NANOTECH_LOCATIONS.values(),
)


def _by_type(*types: SACLocationType) -> dict[str, SACLocation]:
    return {location.name: location for location in LOCATIONS if location.type in types}


ALL_LOCATIONS: dict[str, SACLocation] = {location.name: location for location in LOCATIONS}
# AP location IDs, numbered in LOCATIONS order (which never depends on options), like the item IDs.
# Once SAC is publicly released these are permanent: add new locations at the end of LOCATIONS
# rather than reordering, or every existing seed's IDs shift.
LOCATION_NAME_TO_ID: dict[str, int] = {location.name: BASE_ID + index for index, location in enumerate(LOCATIONS)}
TITANIUM_BOLT_LOCATIONS = _by_type(SACLocationType.TITANIUM_BOLT)
SKILL_POINT_LOCATIONS = _by_type(SACLocationType.SKILL_POINT)
KEYCARD_LOCATIONS = _by_type(SACLocationType.KEYCARD)
ALIEN_CODE_LOCATIONS = _by_type(SACLocationType.ALIEN_CODE)
RATCHET_CHALLENGE_LOCATIONS = _by_type(SACLocationType.RATCHET_CHALLENGE)
BASE_VENDOR_LOCATIONS = _by_type(SACLocationType.VENDOR)
TITAN_VENDOR_LOCATIONS = _by_type(SACLocationType.TITAN_VENDOR)
MOD_VENDOR_LOCATIONS = _by_type(SACLocationType.MOD_VENDOR)

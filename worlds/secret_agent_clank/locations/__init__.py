"""Location tables, assembled from one file per case (locations/<case>.py) -- each case file builds its own CaseLocations bundle (5 dicts, grouped by which options.py toggle/Choice value gates them) using its own fixed id block (see _shared.py), so this module just imports and merges/re-derives from them rather than building anything itself."""
from ..constants import ALIEN_CODES, KEYCARDS
from ..constants.skillpoints import SKILL_POINTS
from ._shared import CaseLocations, SACLocationData
from .a_fiction_full_of_dollars import A_FICTION_FULL_OF_DOLLARS_LOCATIONS
from .asyanica_rooftops import ASYANICA_ROOFTOPS_LOCATIONS
from .azcotal_alley import AZCOTAL_ALLEY_LOCATIONS
from .boltaire_gem_wing import BOLTAIRE_GEM_WING_LOCATIONS
from .boltaire_museum import BOLTAIRE_MUSEUM_LOCATIONS
from .bulkhead_lock import BULKHEAD_LOCK_LOCATIONS
from .countess_villa import COUNTESS_VILLA_LOCATIONS
from .dams_edge_hydrano import DAMS_EDGE_HYDRANO_LOCATIONS
from .galactic_bolt_reserve import GALACTIC_BOLT_RESERVE_LOCATIONS
from .glaciara_ski_slopes import GLACIARA_SKI_SLOPES_LOCATIONS
from .gondola_ascent import GONDOLA_ASCENT_LOCATIONS
from .high_rollers_casino import HIGH_ROLLERS_CASINO_LOCATIONS
from .high_stakes_room import HIGH_STAKES_ROOM_LOCATIONS
from .inside_the_a_eye import INSIDE_THE_A_EYE_LOCATIONS
from .klunks_lair import KLUNKS_LAIR_LOCATIONS
from .larger_than_life import LARGER_THAN_LIFE_LOCATIONS
from .madam_butterqwark import MADAM_BUTTERQWARK_LOCATIONS
from .max_security_cells import MAX_SECURITY_CELLS_LOCATIONS
from .prison_breakout import PRISON_BREAKOUT_LOCATIONS
from .rooftop_deathtrap import ROOFTOP_DEATHTRAP_LOCATIONS
from .saint_qwark import SAINT_QWARK_LOCATIONS
from .spaceship_graveyard import SPACESHIP_GRAVEYARD_LOCATIONS
from .suck_and_jive import SUCK_AND_JIVE_LOCATIONS
from .the_exercise_yard import THE_EXERCISE_YARD_LOCATIONS
from .the_mess_hall import THE_MESS_HALL_LOCATIONS
from .the_quasar_fields import THE_QUASAR_FIELDS_LOCATIONS
from .the_showers import THE_SHOWERS_LOCATIONS
from .underwater_bunker import UNDERWATER_BUNKER_LOCATIONS
from .venantonio_canals import VENANTONIO_CANALS_LOCATIONS
from .venantonio_labs import VENANTONIO_LABS_LOCATIONS

# case_id order.
_CASES: tuple[CaseLocations, ...] = (
    BOLTAIRE_MUSEUM_LOCATIONS,
    BOLTAIRE_GEM_WING_LOCATIONS,
    MAX_SECURITY_CELLS_LOCATIONS,
    ROOFTOP_DEATHTRAP_LOCATIONS,
    ASYANICA_ROOFTOPS_LOCATIONS,
    LARGER_THAN_LIFE_LOCATIONS,
    COUNTESS_VILLA_LOCATIONS,
    GLACIARA_SKI_SLOPES_LOCATIONS,
    THE_MESS_HALL_LOCATIONS,
    AZCOTAL_ALLEY_LOCATIONS,
    GONDOLA_ASCENT_LOCATIONS,
    SUCK_AND_JIVE_LOCATIONS,
    HIGH_ROLLERS_CASINO_LOCATIONS,
    THE_EXERCISE_YARD_LOCATIONS,
    HIGH_STAKES_ROOM_LOCATIONS,
    VENANTONIO_LABS_LOCATIONS,
    VENANTONIO_CANALS_LOCATIONS,
    MADAM_BUTTERQWARK_LOCATIONS,
    GALACTIC_BOLT_RESERVE_LOCATIONS,
    INSIDE_THE_A_EYE_LOCATIONS,
    THE_SHOWERS_LOCATIONS,
    SPACESHIP_GRAVEYARD_LOCATIONS,
    SAINT_QWARK_LOCATIONS,
    THE_QUASAR_FIELDS_LOCATIONS,
    PRISON_BREAKOUT_LOCATIONS,
    DAMS_EDGE_HYDRANO_LOCATIONS,
    A_FICTION_FULL_OF_DOLLARS_LOCATIONS,
    BULKHEAD_LOCK_LOCATIONS,
    UNDERWATER_BUNKER_LOCATIONS,
    KLUNKS_LAIR_LOCATIONS,
)

ALWAYS_ON_LOCATIONS: dict[str, SACLocationData] = {}
STORY_MISSION_LOCATIONS: dict[str, SACLocationData] = {}
ALL_STORY_MISSION_LOCATIONS: dict[str, SACLocationData] = {}
CUTSCENE_LOCATIONS: dict[str, SACLocationData] = {}
_OTHER_LOCATIONS: dict[str, SACLocationData] = {}
for _case in _CASES:
    ALWAYS_ON_LOCATIONS.update(_case.always_on)
    STORY_MISSION_LOCATIONS.update(_case.mission)
    ALL_STORY_MISSION_LOCATIONS.update(_case.all_missions)
    CUTSCENE_LOCATIONS.update(_case.cutscene)
    _OTHER_LOCATIONS.update(_case.other)
del _case

# _OTHER_LOCATIONS mixes 3 independently-toggleable categories (see each
# case file's docstring) -- split back out by exact display name against
# constants/*.py (CaseStructure.__str__ is what generated these names in
# the first place, so this is a lookup, not a second construction pass).
# The id always comes from _OTHER_LOCATIONS (the case files, single source
# of truth) -- only the category-membership decision comes from here.
_SKILL_POINT_NAMES = {str(entry) for entry in SKILL_POINTS}
_KEYCARD_NAMES = {str(entry) for entry in KEYCARDS if entry.case_name != "TODO"}
_ALIEN_CODE_NAMES = {str(entry) for entry in ALIEN_CODES if entry.case_name != "TODO"}

SKILL_POINT_LOCATIONS: dict[str, SACLocationData] = {
    name: data for name, data in _OTHER_LOCATIONS.items() if name in _SKILL_POINT_NAMES
}
KEYCARD_LOCATIONS: dict[str, SACLocationData] = {
    name: data for name, data in _OTHER_LOCATIONS.items() if name in _KEYCARD_NAMES
}
ALIEN_CODE_LOCATIONS: dict[str, SACLocationData] = {
    name: data for name, data in _OTHER_LOCATIONS.items() if name in _ALIEN_CODE_NAMES
}

from ..constants.planets import CASE_NAME_TO_CASE
from ..constants.titanium_bolts import TITANIUM_BOLT_ENTRIES
from ._shared import BASE_ID, CASE_ID_BLOCK_SIZE

# Reserve the end of each case block; existing location IDs stay unchanged.
TITANIUM_BOLT_LOCATIONS = {
    str(entry): SACLocationData(
        BASE_ID + (CASE_NAME_TO_CASE[entry.case_name].case_id - 1) * CASE_ID_BLOCK_SIZE + 900 + index,
        entry.case_name)
    for (_, index), entry in TITANIUM_BOLT_ENTRIES.items()
}
ALWAYS_ON_LOCATIONS.update(TITANIUM_BOLT_LOCATIONS)

ALL_LOCATIONS: dict[str, SACLocationData] = {
    **ALWAYS_ON_LOCATIONS,
    **STORY_MISSION_LOCATIONS,
    **ALL_STORY_MISSION_LOCATIONS,
    **CUTSCENE_LOCATIONS,
    **_OTHER_LOCATIONS,
}

from ..constants.weapon_progression import TITAN_LOCATIONS

TITAN_VENDOR_LOCATIONS = {
    name: SACLocationData(BASE_ID + 31000 + index, "Titan Vendor")
    for index, name in enumerate(TITAN_LOCATIONS.values())
}
ALL_LOCATIONS.update(TITAN_VENDOR_LOCATIONS)

from ..constants.weapon_mods import WEAPON_MODS

MOD_VENDOR_LOCATIONS = {
    mod.location: SACLocationData(BASE_ID + 32000 + mod.mod_id, "Mod Vendor")
    for mod in WEAPON_MODS
}
ALL_LOCATIONS.update(MOD_VENDOR_LOCATIONS)

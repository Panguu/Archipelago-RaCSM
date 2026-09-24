"""Item tables."""
from typing import NamedTuple

from BaseClasses import ItemClassification

from ..constants import (
    CASE_NAME_TO_INFOBOT,
    CHARACTER_ITEM_NAME,
    CLANK_GADGETS,
    GADGETS_FROM_WEAPON_TABLE,
    PLANET_ACCESS_ITEM_NAME,
    PROGRESSIVE_CHARACTER_ITEM_NAME,
    RATCHET_WEAPONS,
    SACCheats,
    SACTraps,
)
from .a_fiction_full_of_dollars import A_FICTION_FULL_OF_DOLLARS_ITEMS
from .asyanica_rooftops import ASYANICA_ROOFTOPS_ITEMS
from .azcotal_alley import AZCOTAL_ALLEY_ITEMS
from .boltaire_gem_wing import BOLTAIRE_GEM_WING_ITEMS
from .boltaire_museum import BOLTAIRE_MUSEUM_ITEMS
from .bulkhead_lock import BULKHEAD_LOCK_ITEMS
from .countess_villa import COUNTESS_VILLA_ITEMS
from .dams_edge_hydrano import DAMS_EDGE_HYDRANO_ITEMS
from .galactic_bolt_reserve import GALACTIC_BOLT_RESERVE_ITEMS
from .glaciara_ski_slopes import GLACIARA_SKI_SLOPES_ITEMS
from .gondola_ascent import GONDOLA_ASCENT_ITEMS
from .high_rollers_casino import HIGH_ROLLERS_CASINO_ITEMS
from .high_stakes_room import HIGH_STAKES_ROOM_ITEMS
from .inside_the_a_eye import INSIDE_THE_A_EYE_ITEMS
from .klunks_lair import KLUNKS_LAIR_ITEMS
from .larger_than_life import LARGER_THAN_LIFE_ITEMS
from .madam_butterqwark import MADAM_BUTTERQWARK_ITEMS
from .max_security_cells import MAX_SECURITY_CELLS_ITEMS
from .prison_breakout import PRISON_BREAKOUT_ITEMS
from .rooftop_deathtrap import ROOFTOP_DEATHTRAP_ITEMS
from .saint_qwark import SAINT_QWARK_ITEMS
from .spaceship_graveyard import SPACESHIP_GRAVEYARD_ITEMS
from .suck_and_jive import SUCK_AND_JIVE_ITEMS
from .the_exercise_yard import THE_EXERCISE_YARD_ITEMS
from .the_mess_hall import THE_MESS_HALL_ITEMS
from .the_quasar_fields import THE_QUASAR_FIELDS_ITEMS
from .the_showers import THE_SHOWERS_ITEMS
from .underwater_bunker import UNDERWATER_BUNKER_ITEMS
from .venantonio_canals import VENANTONIO_CANALS_ITEMS
from .venantonio_labs import VENANTONIO_LABS_ITEMS

BASE_ID = 77_800_000

PROGRESSIVE_PLANET_ITEM_NAME = "Progressive Planet"


class SACItemData(NamedTuple):
    code: int
    classification: ItemClassification


_next_id = BASE_ID

def _table(names: tuple[str, ...], classification: ItemClassification) -> dict[str, SACItemData]:
    global _next_id
    table: dict[str, SACItemData] = {}
    for name in names:
        table[name] = SACItemData(_next_id, classification)
        _next_id += 1
    return table


WEAPON_ITEM_TABLE: dict[str, SACItemData] = _table(RATCHET_WEAPONS, ItemClassification.progression)
# constants/clank_gadgets.py's SACClankGadgets holds two mechanically
# different groups (see that class's docstring): 8 items (clankpda/throwTie/
# CuffLink/TangleVine/FlamethrowerPen/jetboots/HoloKnuckles/superkick) that
# are thematically Clank's, but mechanically live in the SAME WEAPON_ORDER
# struct Ratchet's own weapons live in -- core/core.py's case.ratchet_items
# tracks them, and client/context.py's `ratchet` ownership dict is what
# core/core.py's apply_inventory() expects them in, so they belong in
# WEAPON_ITEM_TABLE, NOT GADGET_ITEM_TABLE below (that table feeds the
# separate `clank` dict, for SACClankGadgets' other 2 items -- BLACK_OUT_PEN/
# THERM_OPTIC_SHADES -- an unrelated, positional Clank inventory system).
WEAPON_ITEM_TABLE.update(_table(GADGETS_FROM_WEAPON_TABLE, ItemClassification.progression))
# constants/weapons.py's RATCHET_WEAPONS no longer includes fountainpen/sunglasses at
# all (they're documented there as the same physical unlock as Black Out Pen/
# Therm-Optic Shades below) -- no popping needed here anymore.
GADGET_ITEM_TABLE: dict[str, SACItemData] = _table(CLANK_GADGETS, ItemClassification.progression)

# Planet access -- two alternative granularities, selected by options.py's
# Infobots choice (world.py's create_items() only ever pools ONE of these
# three tables, never more than one):
#   planets:    PLANET_ACCESS_ITEM_TABLE, one item per planet (coarse).
#   cases:      INFOBOT_ITEM_TABLE, one item per case (fine).
# Progressive Planet option additionally replaces PLANET_ACCESS_ITEM_TABLE
# with repeated copies of a single PROGRESSIVE_PLANET_ITEM_NAME item, each
# copy unlocking the next planet in PLANET_NAMES order -- see world.py.
PLANET_ACCESS_ITEM_TABLE: dict[str, SACItemData] = _table(
    tuple(PLANET_ACCESS_ITEM_NAME.values()), ItemClassification.progression,
)
INFOBOT_ITEM_TABLE: dict[str, SACItemData] = _table(
    tuple(CASE_NAME_TO_INFOBOT.values()), ItemClassification.progression,
)
PROGRESSIVE_PLANET_ITEM_TABLE: dict[str, SACItemData] = _table(
    (PROGRESSIVE_PLANET_ITEM_NAME,), ItemClassification.progression,
)

# Character Items option: Ratchet/Clank get one flat unlock item each;
# Qwark/Gadgetbots are progressive (user: "progressive characters
# specifically for qwark and gadgetbots") -- world.py pools multiple copies
# of each, one per case that character operates (see
# constants/planets.py's CASES_BY_OPERATIVE).
CHARACTER_ITEM_TABLE: dict[str, SACItemData] = _table(
    tuple(CHARACTER_ITEM_NAME.values()), ItemClassification.progression,
)
PROGRESSIVE_CHARACTER_ITEM_TABLE: dict[str, SACItemData] = _table(
    tuple(PROGRESSIVE_CHARACTER_ITEM_NAME.values()), ItemClassification.progression,
)

# Directly grants the "Ratchet Pack" vanilla cheat -- useful, not required
# for anything, so it's not progression.
RATCHET_PACK_ITEM_TABLE: dict[str, SACItemData] = _table((SACCheats.RATCHET_PACK,), ItemClassification.useful)

# Trap items -- force a vanilla cheat on for a duration when received (see
# constants/cheats.py's TRAP_CHEATS/TRAP_DURATIONS). Actual cheat-toggling
# in game memory is still a TODO (CHEATS_ADDRESS layout unconfirmed, see
# core/traps.py).
TRAP_ITEM_TABLE: dict[str, SACItemData] = _table(
    (SACTraps.WEAPON_SWITCHING, SACTraps.MIRRORED_LEVELS, SACTraps.BOLT_CONFUSION, SACTraps.BIG_HEADED),
    ItemClassification.trap,
)

FILLER_ITEM_NAME = "Bolts"
FILLER_ITEM_TABLE: dict[str, SACItemData] = _table((FILLER_ITEM_NAME,), ItemClassification.filler)

# Allocate after existing items to preserve every prior item ID.
PROGRESSIVE_WRENCH_ITEM_NAME = "Progressive Wrench"
PROGRESSIVE_WRENCH_ITEM_TABLE = _table((PROGRESSIVE_WRENCH_ITEM_NAME,), ItemClassification.progression)
for _mod in ("wrenchpower_firebomb", "wrenchpower_triplewave", "wrenchpower_crystallix", "wrenchpower_wildburst"):
    WEAPON_ITEM_TABLE.pop(_mod, None)

# Per-case item tables -- see module docstring, all empty stubs so far.
_PER_CASE_ITEM_TABLES: tuple[dict[str, SACItemData], ...] = (
    BOLTAIRE_MUSEUM_ITEMS, BOLTAIRE_GEM_WING_ITEMS, MAX_SECURITY_CELLS_ITEMS, ROOFTOP_DEATHTRAP_ITEMS,
    ASYANICA_ROOFTOPS_ITEMS, LARGER_THAN_LIFE_ITEMS, COUNTESS_VILLA_ITEMS, GLACIARA_SKI_SLOPES_ITEMS,
    THE_MESS_HALL_ITEMS, AZCOTAL_ALLEY_ITEMS, GONDOLA_ASCENT_ITEMS, SUCK_AND_JIVE_ITEMS,
    HIGH_ROLLERS_CASINO_ITEMS, THE_EXERCISE_YARD_ITEMS, HIGH_STAKES_ROOM_ITEMS, VENANTONIO_LABS_ITEMS,
    VENANTONIO_CANALS_ITEMS, MADAM_BUTTERQWARK_ITEMS, GALACTIC_BOLT_RESERVE_ITEMS, INSIDE_THE_A_EYE_ITEMS,
    THE_SHOWERS_ITEMS, SPACESHIP_GRAVEYARD_ITEMS, SAINT_QWARK_ITEMS, THE_QUASAR_FIELDS_ITEMS,
    PRISON_BREAKOUT_ITEMS, DAMS_EDGE_HYDRANO_ITEMS, A_FICTION_FULL_OF_DOLLARS_ITEMS, BULKHEAD_LOCK_ITEMS,
    UNDERWATER_BUNKER_ITEMS, KLUNKS_LAIR_ITEMS,
)

from ..constants.weapon_progression import PROGRESSIVE_TO_INTERNAL

PROGRESSIVE_WEAPON_ITEM_TABLE = _table(tuple(PROGRESSIVE_TO_INTERNAL), ItemClassification.progression)
from ..constants.weapon_progression import TITAN_ITEMS

# Retain IDs for compatibility with experimental seeds; new seeds use the
# automatic V4-to-V5 bridge and never pool separate Titan Upgrade items.
TITAN_ITEM_TABLE = _table(tuple(TITAN_ITEMS), ItemClassification.progression)

ALL_ITEMS: dict[str, SACItemData] = {
    **TITAN_ITEM_TABLE,
    **PROGRESSIVE_WEAPON_ITEM_TABLE,
    **PROGRESSIVE_WRENCH_ITEM_TABLE,
    **WEAPON_ITEM_TABLE,
    **GADGET_ITEM_TABLE,
    **PLANET_ACCESS_ITEM_TABLE,
    **INFOBOT_ITEM_TABLE,
    **PROGRESSIVE_PLANET_ITEM_TABLE,
    **CHARACTER_ITEM_TABLE,
    **PROGRESSIVE_CHARACTER_ITEM_TABLE,
    **RATCHET_PACK_ITEM_TABLE,
    **TRAP_ITEM_TABLE,
    **FILLER_ITEM_TABLE,
}
for _table_dict in _PER_CASE_ITEM_TABLES:
    ALL_ITEMS.update(_table_dict)
del _table_dict

from ..constants.weapon_mods import WEAPON_MODS

WEAPON_MOD_ITEM_TABLE = _table(tuple(mod.name for mod in WEAPON_MODS), ItemClassification.useful)
ALL_ITEMS.update(WEAPON_MOD_ITEM_TABLE)

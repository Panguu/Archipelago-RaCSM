"""Item tables.

IDs are handed out sequentially in the order the tables below are built, so new
tables must only ever be appended at the end to keep every existing item ID stable.
"""
from itertools import count
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
from ..constants.challenge_mode import PROGRESSIVE_CHALLENGE_MODE
from ..constants.keycards import KEYCARD_ITEMS
from ..constants.weapon_mods import WEAPON_MODS
from ..constants.weapon_progression import PROGRESSIVE_TO_INTERNAL, TITAN_ITEMS

BASE_ID = 77_800_000

PROGRESSIVE_PLANET_ITEM_NAME = "Progressive Planet"


class SACItemData(NamedTuple):
    code: int
    classification: ItemClassification


_next_id = count(BASE_ID)


def _table(names: tuple[str, ...], classification: ItemClassification) -> dict[str, SACItemData]:
    return {name: SACItemData(next(_next_id), classification) for name in names}


WEAPON_ITEM_TABLE: dict[str, SACItemData] = _table(RATCHET_WEAPONS, ItemClassification.progression)
# Clank equipment stored in the WEAPON_ORDER array is tracked alongside Ratchet's
# weapons, so it belongs in WEAPON_ITEM_TABLE. GADGET_ITEM_TABLE is only for the
# Blackout Pen and Therm-Optic Shades, which use a separate inventory.
WEAPON_ITEM_TABLE.update(_table(GADGETS_FROM_WEAPON_TABLE, ItemClassification.progression))
GADGET_ITEM_TABLE: dict[str, SACItemData] = _table(CLANK_GADGETS, ItemClassification.progression)

# Access items; the Infobots option picks which kind is pooled:
#   planets:            one item per planet
#   cases:              one Case File per case
#   progressive_planet: copies of Progressive Planet, each opening the next planet
PLANET_ACCESS_ITEM_TABLE: dict[str, SACItemData] = _table(
    tuple(PLANET_ACCESS_ITEM_NAME.values()), ItemClassification.progression,
)
INFOBOT_ITEM_TABLE: dict[str, SACItemData] = _table(
    tuple(CASE_NAME_TO_INFOBOT.values()), ItemClassification.progression,
)
PROGRESSIVE_PLANET_ITEM_TABLE: dict[str, SACItemData] = _table(
    (PROGRESSIVE_PLANET_ITEM_NAME,), ItemClassification.progression,
)

# Infobots=character_unlocks: one item each for Ratchet and Clank, and one
# progressive copy per case for Qwark and the Gadgetbots.
CHARACTER_ITEM_TABLE: dict[str, SACItemData] = _table(
    tuple(CHARACTER_ITEM_NAME.values()), ItemClassification.progression,
)
PROGRESSIVE_CHARACTER_ITEM_TABLE: dict[str, SACItemData] = _table(
    tuple(PROGRESSIVE_CHARACTER_ITEM_NAME.values()), ItemClassification.progression,
)

# Grants the vanilla "Ratchet Pack" cheat; never required.
RATCHET_PACK_ITEM_TABLE: dict[str, SACItemData] = _table((SACCheats.RATCHET_PACK,), ItemClassification.useful)

# Each trap forces vanilla cheats on for a while (see core/traps.py).
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

PROGRESSIVE_WEAPON_ITEM_TABLE = _table(tuple(PROGRESSIVE_TO_INTERNAL), ItemClassification.progression)

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

WEAPON_MOD_ITEM_TABLE = _table(tuple(mod.name for mod in WEAPON_MODS), ItemClassification.useful)
ALL_ITEMS.update(WEAPON_MOD_ITEM_TABLE)

# Append so all existing item IDs remain stable.
CHALLENGE_MODE_ITEM_TABLE = _table((PROGRESSIVE_CHALLENGE_MODE,), ItemClassification.progression)
ALL_ITEMS.update(CHALLENGE_MODE_ITEM_TABLE)

# Append to preserve IDs from existing seeds.
KEYCARD_ITEM_TABLE = _table(tuple(KEYCARD_ITEMS), ItemClassification.progression)
ALL_ITEMS.update(KEYCARD_ITEM_TABLE)

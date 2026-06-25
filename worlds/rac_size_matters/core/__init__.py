from .address_maps import CURRENT_PLANET_ADDRESS, PLAYER_ADDRS, PLAYER_HEALTH, PLAYER_STATE
from .armour import ARMOUR_FLAG_TO_LOCATION, ARMOUR_SET_CHECKS, ArmourPiece
from .controller import ButtonState
from .display_text import SmallTextBoxAddrs, TextColour, colored_text
from .memory import (
    ARMOUR_ADDRESSES,
    BOLTS,
    GADGETS,
    PLAYER_ARMOUR_SLOTS,
    WEAPONS,
    Int64State,
    MemoryItemState,
    load_weapons_for_planet,
)
from .planets import (
    AUTO_UNLOCK_ADDRESSES,
    BY_ID as PLANETS_BY_ID,
    INFOBOT_ITEM_TO_PLANET,
    INFOBOT_UNLOCK_VALUE,
    PLANET_STATE_ADDRESSES,
)
from .player import PlayerMovementState
from .skill_points import SKILL_POINT_ADDRESS, SKILL_POINTS
from .states.game_state import GameState, PollAddress
from .titanium_bolts import TITANIUM_BOLTS
from .traps import ALL_TRAPS, activate_trap
from .weapons import WEAPON_MAX_LEVELS, WEAPON_MOD_COUNTS

# NOTE: GameOrchestrator/WeaponVendorState/ModVendorState are deliberately NOT
# re-exported here. core.vendor imports from ..items, and items.py imports
# several core submodules — eagerly loading core.vendor (or game_orchestrator,
# which imports it) from this package __init__ creates a circular import
# whenever items.py/world.py import anything from core first. Import those
# two directly from their submodules (core.game_orchestrator / core.vendor).

__all__ = [
    "ARMOUR_ADDRESSES",
    "ARMOUR_FLAG_TO_LOCATION",
    "ARMOUR_SET_CHECKS",
    "ALL_TRAPS",
    "AUTO_UNLOCK_ADDRESSES",
    "ArmourPiece",
    "BOLTS",
    "ButtonState",
    "CURRENT_PLANET_ADDRESS",
    "GADGETS",
    "GameState",
    "INFOBOT_ITEM_TO_PLANET",
    "INFOBOT_UNLOCK_VALUE",
    "Int64State",
    "MemoryItemState",
    "PLANET_STATE_ADDRESSES",
    "PLANETS_BY_ID",
    "PLAYER_ADDRS",
    "PLAYER_ARMOUR_SLOTS",
    "PLAYER_HEALTH",
    "PLAYER_STATE",
    "PlayerMovementState",
    "PollAddress",
    "SKILL_POINT_ADDRESS",
    "SKILL_POINTS",
    "SmallTextBoxAddrs",
    "TITANIUM_BOLTS",
    "TextColour",
    "WEAPON_MAX_LEVELS",
    "WEAPON_MOD_COUNTS",
    "WEAPONS",
    "activate_trap",
    "colored_text",
    "load_weapons_for_planet",
]

"""GLOBALVARS_AddExperience only adds to the saved XP, and the game works out nanotech from it.

GADGET_GetsXP is what levels a weapon up, so Weapon XP stops one point short of the next level.
"""
from dataclasses import dataclass

from ..constants import LEVELLED_INTERNALS, NANOTECH_XP_PERCENT, WEAPON_ORDER, WEAPON_XP_PERCENT, NativeFunctions
from .case_menu import ee_pointer
from .nanotech import read_nanotech
from .patches.asm import jump, packed
from .symbols import require

GADGET_SIZE = 0x74
GADGET_COUNT = 0x28
MAX_LEVELS = 8
_LEVEL = 0x5C
_XP = 0x64
_LEVEL_DEFS = 0x10
_DEF_XP_TO_LEVEL = 0x34
_PLAYER_WEAPON = 0x344


def boost(xp_for_level: int, percent: int) -> int:
    return max(1, xp_for_level * percent // 100)


def boost_nanotech(pine, symbols, operative) -> int:
    """Returns the XP added: 0 at the level cap. Raises ValueError while a level is loading."""
    data = read_nanotech(pine, symbols, operative)
    if data["next_xp"] is None:
        return 0
    gained = boost(data["next_xp"] - data["level_xp"], NANOTECH_XP_PERCENT)
    pine.write_int32(data["xp_address"], data["saved_xp"] + gained)
    return gained


@dataclass(frozen=True)
class EquippedWeapon:
    internal: str
    address: int  # GadgetData
    level: int  # 0-based
    xp: int
    xp_to_level: int  # 0 at max level


def equipped_weapon(pine, symbols, player: int) -> EquippedWeapon | None:
    """None if `player` isn't holding a weapon that has levels."""
    getter, get_data, gadgets = require(symbols, NativeFunctions.WEAPON_GET_CURRENT_WEAPON,
                                        NativeFunctions.GADGET_GET_DATA, "GADGET_g_GadgetList")
    # WEAPON_GetCurrWeap(player) is GADGET_GetData(player->0x344).
    if pine.read_bytes(getter, 16) != packed([0x27BDFFF0, 0xFFBF0000, jump(get_data, True),
                                              0x8C840000 | _PLAYER_WEAPON]):
        raise RuntimeError("Native current-weapon getter changed")
    gadget = pine.read_int32(player + _PLAYER_WEAPON)
    if gadget >= GADGET_COUNT or WEAPON_ORDER[gadget] is None:
        return None
    return _weapon(pine, gadgets, gadget)


def owned_weapons(pine, symbols, owned: dict[str, bool]) -> list[EquippedWeapon]:
    """Every owned Ratchet and Clank weapon that levels up."""
    gadgets = require(symbols, "GADGET_g_GadgetList")
    weapons = (_weapon(pine, gadgets, gadget) for gadget, internal in enumerate(WEAPON_ORDER)
               if internal in LEVELLED_INTERNALS and owned.get(internal))
    return [weapon for weapon in weapons if weapon is not None]


def _weapon(pine, gadgets: int, gadget: int) -> EquippedWeapon | None:
    address = gadgets + gadget * GADGET_SIZE
    level, xp = pine.read_int32(address + _LEVEL), pine.read_int32(address + _XP)
    if level + 1 >= MAX_LEVELS:
        return EquippedWeapon(WEAPON_ORDER[gadget], address, level, xp, 0)
    definition = pine.read_int32(address + _LEVEL_DEFS + level * 4)
    if not ee_pointer(definition, _DEF_XP_TO_LEVEL + 4):
        return None  # a gadget or tool, not a levelled weapon
    return EquippedWeapon(WEAPON_ORDER[gadget], address, level, xp,
                          pine.read_int32(definition + _DEF_XP_TO_LEVEL))


def boost_weapon(pine, weapon: EquippedWeapon) -> int:
    """Returns the XP added."""
    if not weapon.xp_to_level:
        return 0
    xp = min(weapon.xp + boost(weapon.xp_to_level, WEAPON_XP_PERCENT), weapon.xp_to_level - 1)
    if xp <= weapon.xp:
        return 0
    pine.write_int32(weapon.address + _XP, xp)
    return xp - weapon.xp

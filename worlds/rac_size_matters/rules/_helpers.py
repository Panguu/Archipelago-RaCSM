from __future__ import annotations


from ..core.weapons import WEAPON_DATA
from ..items import PROGRESSIVE_ARMOUR_NAME, PROGRESSIVE_WEAPON_NAME, WEAPON_DISPLAY_TO_INTERNAL
from rule_builder.rules import And, Has, HasAny, HasAnyCount

_PROJECTILE_WEAPONS = [
    display for display, internal in WEAPON_DISPLAY_TO_INTERNAL.items()
    if WEAPON_DATA[internal].is_projectile
]
_PROJECTILE_WEAPONS_ALL_NAMES = [
    *_PROJECTILE_WEAPONS, *(PROGRESSIVE_WEAPON_NAME[name] for name in _PROJECTILE_WEAPONS),
]

# Piece index is positional (1-indexed), matching ARMOUR_PIECE_BITMASKS order in items.py.
_ARMOUR_PIECE_INDEX: dict[str, int] = {"Chestplate": 1, "Helmet": 2, "Gloves": 3, "Boots": 4}

def HasProjectileWeapon() -> HasAny:
    return HasAny(*_PROJECTILE_WEAPONS_ALL_NAMES)

def HasArmourPiece(set_display: str, piece_name: str) -> HasAnyCount:
    return HasAnyCount({
        f"{set_display} {piece_name}": 1,
        PROGRESSIVE_ARMOUR_NAME[set_display]: _ARMOUR_PIECE_INDEX[piece_name],
    })
def HasWeapon(weapon: str) -> HasAny:
    return HasAny(weapon, PROGRESSIVE_WEAPON_NAME[weapon])

def HasArmourSet(set_display: str) -> And:
    return And(*(HasArmourPiece(set_display, piece) for piece in _ARMOUR_PIECE_INDEX))

def HasGadget(gadget: str) -> HasAny:
    return HasAny(gadget)

def HasInfobot(infobot: str) -> HasAny:
    return Has(infobot)

def has_projectile_weapon(state, player: int) -> bool:
    return state.has_any(_PROJECTILE_WEAPONS_ALL_NAMES, player)


def infobot(item_name: str, player: int):
    return lambda state: state.has(item_name, player)


def has_weapon(state, player: int, weapon: str) -> bool:
    return state.has(weapon, player) or state.has(PROGRESSIVE_WEAPON_NAME[weapon], player)

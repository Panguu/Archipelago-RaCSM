from __future__ import annotations


from ..constants import Rac5Gadgets, Rac5Infobots
from ..core.weapons import WEAPON_DATA
from ..items import PROGRESSIVE_ARMOUR_NAME, PROGRESSIVE_WEAPON_NAME, WEAPON_DISPLAY_TO_INTERNAL
from rule_builder.rules import And, Has, HasAll, HasAny, HasAnyCount, Or

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

def HasGoodExpPlanet() -> Or:
    return Or(
        HasAll(Rac5Infobots.QUODRONA, Rac5Gadgets.SHRINK_RAY),
        HasAll(Rac5Infobots.DAYNI_MOON, Rac5Gadgets.SPROUT_O_MATIC),
        HasAll(Rac5Infobots.CHALLAX, Rac5Gadgets.POLARIZER),
        HasAll(Rac5Infobots.OUTPOST_OMEGA, Rac5Gadgets.HYPERSHOT, Rac5Gadgets.SPROUT_O_MATIC),
    )

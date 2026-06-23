from __future__ import annotations

from ..address_maps import ARMOUR_BASE, TITANIUM_BOLT_BASE, WEAPON_ARRAY_BASE_BY_PLANET
from ..armour import ArmourAddresses, ArmourPiece
from ..titanium_bolts import TitaniumBoltAddresses
from ..weapons import GadgetAddresses, WeaponAddresses, build_weapons

WEAPONS: dict[str, WeaponAddresses] = {}
GADGETS: dict[str, GadgetAddresses] = {}

_armour              = ArmourAddresses(ARMOUR_BASE)
ARMOUR_ADDRESSES:    dict[str, int] = _armour.sets
PLAYER_ARMOUR_SLOTS: dict[str, int] = _armour.slots

BOLTS = TitaniumBoltAddresses(TITANIUM_BOLT_BASE)

_ARMOUR_PIECES = [ArmourPiece.CHESTPLATE, ArmourPiece.HELMET, ArmourPiece.GLOVES, ArmourPiece.BOOTS]
_PIECE_TO_SLOTS: dict[ArmourPiece, list[str]] = {
    ArmourPiece.CHESTPLATE: ["chestplate"],
    ArmourPiece.HELMET:     ["helmet"],
    ArmourPiece.GLOVES:     ["gloves_left", "gloves_right"],
    ArmourPiece.BOOTS:      ["boots_left", "boots_right"],
}
_ARMOUR_SET_ORDER = ["wildfire", "sludge", "crystallix", "electroshock", "mega_bomb", "hyperborean", "chameleon"]


def load_weapons_for_planet(planet_id: int) -> bool:
    WEAPONS.clear()
    GADGETS.clear()
    array_base = WEAPON_ARRAY_BASE_BY_PLANET.get(planet_id)
    if array_base is None:
        return False
    weapons, gadgets = build_weapons(array_base)
    WEAPONS.update(weapons)
    GADGETS.update(gadgets)
    return True

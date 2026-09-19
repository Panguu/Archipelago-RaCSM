"""Only native multi-level weapons participate; tools stay single unlocks."""
from .clank_gadgets import SACClankWeapons, SACProgressiveClankWeapons, SACProtoWeapons
from .vendor import vendor_location_name
from .weapons import (
    EQUIPMENT_DISPLAY_TO_INTERNAL,
    SACProgressiveRatchetWeapons,
    SACRatchetWeapons,
    SACTitanWeapons,
)

LEVELLED_INTERNALS = ("blaster", "shardgun", "beemineglove", "shockrocket",
    "walloper", "plasmawhip", "porkbomb", "minelauncher", "ryno", "throwTie",
    "CuffLink", "TangleVine", "HoloKnuckles", "FlamethrowerPen", "LightningUmbrella")


def _attrs(cls):
    return {name: value for name, value in vars(cls).items() if not name.startswith("_")}


# Unlock -> progressive display name, matched by shared class attribute name
# (e.g. SACRatchetWeapons.SHOCKROCKET <-> SACProgressiveRatchetWeapons.SHOCKROCKET)
# rather than string surgery on the display name itself, which broke once the
# "Unlock: {character} {weapon}" naming scheme was replaced by "Weapon:
# {character}: {weapon}" (see constants/weapons.py, constants/clank_gadgets.py).
_UNLOCK_ATTRS = {**_attrs(SACRatchetWeapons), **_attrs(SACClankWeapons)}
_PROGRESSIVE_ATTRS = {**_attrs(SACProgressiveRatchetWeapons), **_attrs(SACProgressiveClankWeapons)}

UNLOCK_TO_PROGRESSIVE = {
    _UNLOCK_ATTRS[attr]: _PROGRESSIVE_ATTRS[attr]
    for attr in _PROGRESSIVE_ATTRS
    if attr in _UNLOCK_ATTRS and EQUIPMENT_DISPLAY_TO_INTERNAL.get(_UNLOCK_ATTRS[attr]) in LEVELLED_INTERNALS
}
PROGRESSIVE_TO_INTERNAL = {
    progressive: EQUIPMENT_DISPLAY_TO_INTERNAL[unlock] for unlock, progressive in UNLOCK_TO_PROGRESSIVE.items()
}
def max_level(internal, ng_plus):
    return 4 if internal == "ryno" or not ng_plus else 8

# Unlock display name -> Titan/Proto display name, matched by shared class
# attribute name (same pattern as UNLOCK_TO_PROGRESSIVE above).
_TITAN_ATTRS = {**_attrs(SACTitanWeapons), **_attrs(SACProtoWeapons)}
_UNLOCK_TO_TITAN = {
    _UNLOCK_ATTRS[attr]: _TITAN_ATTRS[attr]
    for attr in _TITAN_ATTRS if attr in _UNLOCK_ATTRS
}

TITAN_LOCATIONS = {
    EQUIPMENT_DISPLAY_TO_INTERNAL[unlock]: vendor_location_name(titan)
    for unlock, titan in _UNLOCK_TO_TITAN.items()
}
TITAN_ITEMS = {f"Titan Upgrade: {titan}": EQUIPMENT_DISPLAY_TO_INTERNAL[unlock]
               for unlock, titan in _UNLOCK_TO_TITAN.items()}

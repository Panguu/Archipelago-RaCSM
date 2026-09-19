from ...constants.clank_gadgets import SACClankGadgets
from ...constants.vendor import VENDOR_WEAPONS
from ...constants.weapons import EQUIPMENT_DISPLAY_TO_INTERNAL
from ..inventories.weapons import WEAPON_ORDER, WeaponSlot

VENDOR_LOCATIONS = {
    WeaponSlot(WEAPON_ORDER.index(EQUIPMENT_DISPLAY_TO_INTERNAL[name])): EQUIPMENT_DISPLAY_TO_INTERNAL[name]
    for name in VENDOR_WEAPONS
}

_PICKUP_SLOTS = (
    WeaponSlot.BLASTER, WeaponSlot.SHARDGUN, WeaponSlot.BEEMINEGLOVE, WeaponSlot.WALLOPER,
    WeaponSlot.MINELAUNCHER, WeaponSlot.THROWTIE, WeaponSlot.CUFFLINK, WeaponSlot.TANGLEVINE,
    WeaponSlot.FLAMETHROWERPEN,
    WeaponSlot.HOLOMONOCLE, WeaponSlot.JETBOOTS, WeaponSlot.OMNIKEY,
)
PICKUP_LOCATIONS = {slot: WEAPON_ORDER[slot] for slot in _PICKUP_SLOTS}
PICKUP_LOCATIONS[WeaponSlot.FOUNTAINPEN] = f"{SACClankGadgets.BLACK_OUT_PEN} (Pickup)"

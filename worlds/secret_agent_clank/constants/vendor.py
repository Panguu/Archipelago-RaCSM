"""SAC has exactly one native shop (reached from Clank's pause menu). Base weapon/
gadget offers, weapon mods (weapon_mods.py) and Titan/Proto upgrades
(weapon_progression.py) are split into separate constant groups purely for code
organization, not because there are multiple in-game vendors -- every vendor-purchase
location shares the same "Vendor: {item}" naming regardless of group."""
from dataclasses import dataclass

from .clank_gadgets import SACClankGadgets, SACClankWeapons
from .weapons import SACRatchetWeapons

VENDOR_LOCATION_PREFIX = "Vendor: "


def vendor_location_name(display_name: str) -> str:
    return f"{VENDOR_LOCATION_PREFIX}{display_name}"


@dataclass(frozen=True)
class SACVendorWeapons:
    """WEAPON_ORDER-struct weapons/gadgets whose ONLY native source is the vendor --
    see core/patches/locations.py's VENDOR_LOCATIONS (native slot lookup) and
    rules/vendor_access.py's VENDOR_ONLY_ITEM_NAMES (display-name gating)."""
    SHOCKROCKET       = SACRatchetWeapons.SHOCKROCKET
    PLASMAWHIP        = SACRatchetWeapons.PLASMAWHIP
    PORKBOMB          = SACRatchetWeapons.PORKBOMB
    RYNO              = SACRatchetWeapons.RYNO
    KICKBLAST         = SACRatchetWeapons.KICKBLAST
    HOLOKNUCKLES      = SACClankWeapons.HOLOKNUCKLES
    LIGHTNINGUMBRELLA = SACClankWeapons.LIGHTNINGUMBRELLA
    SUPERKICK         = SACClankWeapons.SUPERKICK
    KICKSPLOSION      = SACClankWeapons.KICKSPLOSION
    HYPNOWATCH        = SACClankGadgets.HYPNOWATCH
    CLANKPDA          = SACClankGadgets.CLANKPDA
    BOLTGRABBER       = SACClankGadgets.BOLTGRABBER


VENDOR_WEAPONS: tuple[str, ...] = tuple(
    value for name, value in vars(SACVendorWeapons).items() if not name.startswith("_")
)

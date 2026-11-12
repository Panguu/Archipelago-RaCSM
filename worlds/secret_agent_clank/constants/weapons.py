from dataclasses import dataclass

from .clank_gadgets import SACClankGadgets, SACClankWeapons
from .weapon_order import WEAPON_ORDER, WeaponSlot


@dataclass(frozen=True)
class SACRatchetWeapons:
    SHOCKROCKET       = "Shock Rocket (Ratchet)"
    PLASMAWHIP        = "Plasma Whip (Ratchet)"
    PORKBOMB          = "Pork Bomb Gun (Ratchet)"
    BLASTER           = "Dual Lacerators (Ratchet)"
    SHARDGUN          = "Shard Gun (Ratchet)"
    BEEMINEGLOVE      = "Bee Mine Mk. II (Ratchet)"
    WALLOPER          = "Walloper (Ratchet)"
    MINELAUNCHER      = "Mine Launcher (Ratchet)"
    RATCHETPDA        = "Gadgetron PDA (Ratchet)"
    BOLTTRANSFER      = "Bolt Extractor (Ratchet)"
    RYNO              = "RYNO (Ratchet)"


@dataclass(frozen=True)
class SACProgressiveRatchetWeapons:
    SHOCKROCKET       = "Progressive Shock Rocket (Ratchet)"
    PLASMAWHIP        = "Progressive Plasma Whip (Ratchet)"
    PORKBOMB          = "Progressive Pork Bomb Gun (Ratchet)"
    BLASTER           = "Progressive Dual Lacerators (Ratchet)"
    SHARDGUN          = "Progressive Shard Gun (Ratchet)"
    BEEMINEGLOVE      = "Progressive Bee Mine Mk. II (Ratchet)"
    WALLOPER          = "Progressive Walloper (Ratchet)"
    MINELAUNCHER      = "Progressive Mine Launcher (Ratchet)"
    RATCHETPDA        = "Progressive Agency PDA (Ratchet)"
    BOLTTRANSFER      = "Progressive Bolt Transfer (Ratchet)"
    RYNO              = "Progressive RYNO (Ratchet)"


@dataclass(frozen=True)
class SACTitanWeapons:
    """The NG+ Titan upgrades, for the Ratchet weapons that have one. Each shares its
    attribute name with the SACRatchetWeapons entry it upgrades."""
    SHOCKROCKET  = "Titan Electro Rocket (Ratchet)"
    PLASMAWHIP   = "Titan Plasma Cord (Ratchet)"
    PORKBOMB     = "Titan Meat Mortar (Ratchet)"
    BLASTER      = "Titan Dual Vindicators (Ratchet)"
    SHARDGUN     = "Titan Shard Cannon (Ratchet)"
    BEEMINEGLOVE = "Titan Killer Bee Mine (Ratchet)"
    WALLOPER     = "Titan Marauder (Ratchet)"
    MINELAUNCHER = "Titan Ordnance Launcher (Ratchet)"


@dataclass(frozen=True)
class SACQwarkWeapons:
    """Qwark's weapons. Not randomized; listed for reference only."""
    QWARKBLASTER      = "Blaster (Qwark)"
    GIANTQWARKBLASTER = "Giant Blaster (Qwark)"


RATCHET_WEAPONS: tuple[str, ...] = (
    SACRatchetWeapons.SHOCKROCKET,
    SACRatchetWeapons.PLASMAWHIP,
    SACRatchetWeapons.PORKBOMB,
    SACRatchetWeapons.BLASTER,
    SACRatchetWeapons.SHARDGUN,
    SACRatchetWeapons.BEEMINEGLOVE,
    SACRatchetWeapons.WALLOPER,
    SACRatchetWeapons.MINELAUNCHER,
    SACRatchetWeapons.RATCHETPDA,
    SACRatchetWeapons.BOLTTRANSFER,
    SACRatchetWeapons.RYNO,
)
GADGETS_FROM_WEAPON_TABLE: tuple[str, ...] = (
    SACClankGadgets.CLANKPDA,
    SACClankGadgets.JETBOOTS,
    SACClankGadgets.OMNIKEY,
    SACClankGadgets.HYPNOWATCH,
    SACClankGadgets.HOLOMONOCLE,
    SACClankGadgets.BOLTGRABBER,
    SACClankWeapons.THROWTIE,
    SACClankWeapons.CUFFLINK,
    SACClankWeapons.TANGLEVINE,
    SACClankWeapons.FLAMETHROWERPEN,
    SACClankWeapons.HOLOKNUCKLES,
    SACClankWeapons.SUPERKICK,
    SACClankWeapons.KICKBLAST,
    SACClankWeapons.LIGHTNINGUMBRELLA,
    SACClankWeapons.KICKSPLOSION,
)

EQUIPMENT_DISPLAY_TO_INTERNAL: dict[str, str] = {
    display: WEAPON_ORDER[WeaponSlot[attr]]
    for cls in (SACRatchetWeapons, SACClankGadgets, SACClankWeapons)
    for attr, display in vars(cls).items()
    if display in (*RATCHET_WEAPONS, *GADGETS_FROM_WEAPON_TABLE)
}
EQUIPMENT_INTERNAL_TO_DISPLAY = {
    internal: display for display, internal in EQUIPMENT_DISPLAY_TO_INTERNAL.items()
}
CLANK_PICKUP_TO_INTERNAL = {
    SACClankGadgets.BLACK_OUT_PEN: "fountainpen",
    SACClankGadgets.THERM_OPTIC_SHADES: "sunglasses",
}

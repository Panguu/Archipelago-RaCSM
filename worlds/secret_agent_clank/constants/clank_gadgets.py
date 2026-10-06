"""Clank item names."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SACClankWeapons:
    """Clank weapons stored in the WEAPON_ORDER array; most have progressive and Proto tiers."""
    THROWTIE          = "Tie-A-Rang (Clank)"
    CUFFLINK          = "Cufflink Bomb (Clank)"
    TANGLEVINE        = "Tanglevine Carnation (Clank)"
    FLAMETHROWERPEN   = "Blowtorch Briefcase (Clank)"
    HOLOKNUCKLES      = "Holo-Knuckles (Clank)"
    SUPERKICK         = "Clank Fu Kick (Clank)"
    LIGHTNINGUMBRELLA = "Thunderstorm Umbrella (Clank)"
    KICKSPLOSION      = "Hot Foot 2.1 Beta (Clank)"


@dataclass(frozen=True)
class SACProgressiveClankWeapons:
    """Progressive-item counterpart to SACClankWeapons."""
    THROWTIE          = "Progressive Tie-A-Rang (Clank)"
    CUFFLINK          = "Progressive Cufflink Bomb (Clank)"
    TANGLEVINE        = "Progressive Tanglevine Carnation (Clank)"
    FLAMETHROWERPEN   = "Progressive Blowtorch Briefcase (Clank)"
    HOLOKNUCKLES      = "Progressive Holo-Knuckles (Clank)"
    LIGHTNINGUMBRELLA = "Progressive Thunderstorm Umbrella (Clank)"


@dataclass(frozen=True)
class SACProtoWeapons:
    """NG+ Proto upgrades, paired with SACClankWeapons by shared attribute name."""
    THROWTIE          = "Proto Whirlwind Throwtie (Clank)"
    CUFFLINK          = "Proto Wrist Mortar (Clank)"
    TANGLEVINE        = "Proto Kudzu Tangle (Clank)"
    FLAMETHROWERPEN   = "Proto Hellfire Haversack (Clank)"
    HOLOKNUCKLES      = "Proto Hardlight Fist (Clank)"
    LIGHTNINGUMBRELLA = "Proto Lightning Rod (Clank)"


@dataclass(frozen=True)
class SACClankGadgets:
    """Clank gadgets with no upgrade tiers.

    Blackout Pen and Therm-Optic Shades are tracked by CLANK_GADGET_BY_CASE_ID;
    the rest live in the WEAPON_ORDER array like the weapons.
    """

    BLACK_OUT_PEN      = "Blackout Pen (Clank)"
    THERM_OPTIC_SHADES = "Therm-Optic Shades (Clank)"
    CLANKPDA           = "Agency PDA (Clank)"
    JETBOOTS           = "Jet Boots (Clank)"
    OMNIKEY            = "Omni-Key 5000 (Clank)"
    HYPNOWATCH         = "Hypno-Watch (Clank)"
    HOLOMONOCLE        = "Holo-Monocle (Clank)"
    BOLTGRABBER        = "Bolt Grabber (Clank)"


# case_id -> Clank gadgets picked up there that are not in the WEAPON_ORDER array.
CLANK_GADGET_BY_CASE_ID: dict[int, tuple[str, ...]] = {
    1: (SACClankGadgets.BLACK_OUT_PEN, SACClankGadgets.THERM_OPTIC_SHADES),  # Boltaire Museum
}

# Flattened in CLANK_GADGET_BY_CASE_ID order; this order fixes their item IDs.
CLANK_GADGETS: tuple[str, ...] = tuple(
    gadget for gadgets in CLANK_GADGET_BY_CASE_ID.values() for gadget in gadgets
)


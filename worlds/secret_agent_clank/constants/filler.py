from dataclasses import dataclass


@dataclass(frozen=True)
class SACFiller:
    BOLTS = "Bolts"
    NANOTECH_XP = "Nanotech XP"
    WEAPON_XP = "Weapon XP"


ALL_FILLER: tuple[str, ...] = (SACFiller.BOLTS, SACFiller.NANOTECH_XP, SACFiller.WEAPON_XP)
NANOTECH_XP_PERCENT = 25
WEAPON_XP_PERCENT = 25

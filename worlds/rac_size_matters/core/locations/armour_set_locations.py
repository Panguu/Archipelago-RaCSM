from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...constants import Rac5ArmourSet
from ..armour import ArmourSet

if TYPE_CHECKING:
    from ..armour import ArmourUnlocks, EquippedArmour


@dataclass(frozen=True)
class ArmourSetCheck:
    chestplate: ArmourSet | None = None
    helmet: ArmourSet | None = None
    gloves: ArmourSet | None = None
    boots: ArmourSet | None = None

    def required_mask(self) -> int:
        mask = 0
        for val in {self.chestplate, self.helmet, self.gloves, self.boots} - {None}:
            mask |= 1 << (val - 1)
        return mask

    def is_unlocked(self, unlocks: ArmourUnlocks) -> bool:
        """True if every base armour set this cosmetic combo requires is fully owned."""
        required = self.required_mask()
        return (required & unlocks.owned_mask()) == required

    def matches(self, equipped: EquippedArmour) -> bool:
        """True if the currently equipped pieces match this combo exactly."""
        if self.chestplate is not None and equipped.chestplate != self.chestplate:
            return False
        if self.helmet is not None and equipped.helmet != self.helmet:
            return False
        if self.gloves is not None:
            if equipped.gloves_left != self.gloves or equipped.gloves_right != self.gloves:
                return False
        if self.boots is not None:
            if equipped.boots_left != self.boots or equipped.boots_right != self.boots:
                return False
        return True


ARMOUR_SET_CHECKS: dict[str, ArmourSetCheck] = {
    Rac5ArmourSet.WILDFIRE: ArmourSetCheck(
        chestplate=ArmourSet.Wildfire,
        helmet=ArmourSet.Wildfire,
        gloves=ArmourSet.Wildfire,
        boots=ArmourSet.Wildfire,
    ),
    Rac5ArmourSet.WILDBURST: ArmourSetCheck(
        chestplate=ArmourSet.Wildfire, helmet=ArmourSet.Sludge, gloves=ArmourSet.Wildfire, boots=ArmourSet.Wildfire
    ),
    Rac5ArmourSet.SLUDGE_MK9: ArmourSetCheck(
        chestplate=ArmourSet.Sludge, helmet=ArmourSet.Sludge, gloves=ArmourSet.Sludge, boots=ArmourSet.Sludge
    ),
    Rac5ArmourSet.CRYSTALLIX: ArmourSetCheck(
        chestplate=ArmourSet.Crystallix,
        helmet=ArmourSet.Crystallix,
        gloves=ArmourSet.Crystallix,
        boots=ArmourSet.Crystallix,
    ),
    Rac5ArmourSet.TRIPLE_WAVE: ArmourSetCheck(
        chestplate=ArmourSet.Electroshock,
        helmet=ArmourSet.Wildfire,
        gloves=ArmourSet.Sludge,
        boots=ArmourSet.Electroshock,
    ),
    Rac5ArmourSet.SHOCK_CRYSTAL: ArmourSetCheck(
        chestplate=ArmourSet.Crystallix,
        helmet=ArmourSet.Electroshock,
        gloves=ArmourSet.Crystallix,
        boots=ArmourSet.Electroshock,
    ),
    Rac5ArmourSet.ELECTROSHOCK: ArmourSetCheck(
        chestplate=ArmourSet.Electroshock,
        helmet=ArmourSet.Electroshock,
        gloves=ArmourSet.Electroshock,
        boots=ArmourSet.Electroshock,
    ),
    Rac5ArmourSet.MEGA_BOMB: ArmourSetCheck(
        chestplate=ArmourSet.MegaBomb,
        helmet=ArmourSet.MegaBomb,
        gloves=ArmourSet.MegaBomb,
        boots=ArmourSet.MegaBomb,
    ),
    Rac5ArmourSet.FIRE_BOMB: ArmourSetCheck(
        chestplate=ArmourSet.MegaBomb,
        helmet=ArmourSet.MegaBomb,
        gloves=ArmourSet.Wildfire,
        boots=ArmourSet.MegaBomb,
    ),
    Rac5ArmourSet.HYPERBOREAN: ArmourSetCheck(
        chestplate=ArmourSet.Hyperborean,
        helmet=ArmourSet.Hyperborean,
        gloves=ArmourSet.Hyperborean,
        boots=ArmourSet.Hyperborean,
    ),
    Rac5ArmourSet.ICE_II: ArmourSetCheck(
        chestplate=ArmourSet.Hyperborean,
        helmet=ArmourSet.Crystallix,
        gloves=ArmourSet.Hyperborean,
        boots=ArmourSet.Hyperborean,
    ),
    Rac5ArmourSet.CHAMELEON: ArmourSetCheck(
        chestplate=ArmourSet.Chameleon,
        helmet=ArmourSet.Chameleon,
        gloves=ArmourSet.Chameleon,
        boots=ArmourSet.Chameleon,
    ),
    Rac5ArmourSet.STALKER: ArmourSetCheck(
        chestplate=ArmourSet.Chameleon,
        helmet=ArmourSet.Wildfire,
        gloves=ArmourSet.Sludge,
        boots=ArmourSet.Chameleon,
    ),
}

_HYBRID_BYTE1_BITS: dict[str, int] = {
    Rac5ArmourSet.SHOCK_CRYSTAL: 0x01,
    Rac5ArmourSet.WILDBURST: 0x02,
    Rac5ArmourSet.TRIPLE_WAVE: 0x04,
    Rac5ArmourSet.ICE_II: 0x08,
    Rac5ArmourSet.STALKER: 0x10,
}

ARMOUR_SET_CHECK_MASKS: dict[str, int] = {
    name: (_HYBRID_BYTE1_BITS[name] << 8) if name in _HYBRID_BYTE1_BITS else check.required_mask()
    for name, check in ARMOUR_SET_CHECKS.items()
}

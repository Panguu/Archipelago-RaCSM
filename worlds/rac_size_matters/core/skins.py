from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from .structs.game import SkinStruct

if TYPE_CHECKING:
    from ..interface_orchestrator.memory.accessor import MemoryAccessor


# Data

@dataclass(frozen=True)
class SkinData:
    unlock_mask: int | None
    equip_id:    int


class Skin(Enum):
    """
    Player Skin Enum
    These are the values of unlocked and equiped values for skins.
    """
    DEFAULT          = SkinData(unlock_mask=0x01, equip_id=0x00)
    PIRATE_RATCHET   = SkinData(unlock_mask=0x02, equip_id=0x01)
    GODZILLA_RATCHET = SkinData(unlock_mask=0x04, equip_id=0x02)
    TRASH_RATCHET    = SkinData(unlock_mask=None,  equip_id=0x03)
    SWIM_RATCHET     = SkinData(unlock_mask=0x10,  equip_id=0x04)
    KANGA_RATCHET    = SkinData(unlock_mask=0x20,  equip_id=0x05)
    HIRO_RATCHET     = SkinData(unlock_mask=0x40,  equip_id=0x06)

    @property
    def unlock_mask(self) -> int | None:
        return self.value.unlock_mask

    @property
    def equip_id(self) -> int:
        return self.value.equip_id


SKIN_BY_EQUIP_ID: dict[int, Skin] = {s.equip_id: s for s in Skin}
ALL_SKINS_UNLOCK_MASK: int = 0x01 | 0x02 | 0x04 | 0x10 | 0x20 | 0x40


# State (runtime)

class SkinState:

    def __init__(self) -> None:
        self._skin: Skin = Skin.DEFAULT

    def set_skin(self, skin: Skin) -> None:
        self._skin = skin

    def set_skin_by_option(self, value: int) -> None:
        self._skin = SKIN_BY_EQUIP_ID.get(value, Skin.DEFAULT)

    def apply(self, accessor: MemoryAccessor) -> None:
        accessor.write_field(SkinStruct, "unlocked", ALL_SKINS_UNLOCK_MASK)
        accessor.write_field(SkinStruct, "equipped", self._skin.equip_id)

    def __repr__(self) -> str:
        return f"SkinState(skin={self._skin.name})"

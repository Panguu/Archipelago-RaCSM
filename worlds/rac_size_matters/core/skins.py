from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from .structs.game import SkinStruct

if TYPE_CHECKING:
    from ..pypine import Pine


@dataclass(frozen=True)
class SkinData:
    unlock_mask: int | None
    equip_id:    int


class Skin(Enum):
    """Unlock mask / equip id pairs for each player skin."""
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


class SkinSlot:
    """Pine-backed accessor for one SkinStruct field (unlocked bitmask or equipped id)."""

    def __init__(self, field: str) -> None:
        self.field = field
        self.address = SkinStruct.address_of(field)

    def __get__(self, instance, owner) -> int | None:
        if instance is None:
            return None
        return instance.pine.read_int8(self.address)

    def __set__(self, instance, value: int) -> None:
        if instance is None:
            return
        instance.pine.write_int8(self.address, value)

    def __delete__(self, instance) -> None:
        if instance is None:
            return
        instance.pine.write_int8(self.address, 0)


class SkinInventory:
    """Pine-backed live accessor for the equipped/unlocked skin bytes, replacing SkinState."""

    unlocked = SkinSlot("unlocked")
    equipped = SkinSlot("equipped")

    def __init__(self, pine: Pine) -> None:
        self.pine = pine
        self._skin: Skin = Skin.DEFAULT

    def get(self) -> Skin:
        return SKIN_BY_EQUIP_ID.get(self.equipped, Skin.DEFAULT)

    def set(self, skin: Skin) -> None:
        self._skin = skin
        self.equipped = skin.equip_id
        self.unlocked = ALL_SKINS_UNLOCK_MASK

    def set_by_option(self, value: int) -> None:
        self.set(SKIN_BY_EQUIP_ID.get(value, Skin.DEFAULT))

    def delete(self) -> None:
        self.set(Skin.DEFAULT)

    def setup(self) -> None:
        """Write the currently selected skin's unlock/equip bytes into game memory."""
        self.equipped = self._skin.equip_id
        self.unlocked = ALL_SKINS_UNLOCK_MASK

    def __repr__(self) -> str:
        return f"SkinInventory(skin={self._skin.name})"

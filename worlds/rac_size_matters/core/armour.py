from __future__ import annotations

from collections.abc import Callable
from enum import IntEnum, IntFlag
from typing import NamedTuple

from ..constants import (
    Rac5ClankChallenges as RACSMCLANK,
    Rac5Locations,
    Rac5Planets,
    Rac5SkyboardChallenges as RACSMSKY,
)
from ..pypine import Pine
from .states.base_state import BaseState
from .structs.pickups import ArmourStruct

# Armour address resolvers
_BOOTS_MASK = 0xF0  # module-level, not inside the enum body


class ArmourSet(IntEnum):
    """
    Enum representing different armour sets in the game.
    This is the value which is set in armour slots to represent what armour is currently equiped.
    """

    Wildfire = 1
    Sludge = 2
    Crystallix = 3
    Electroshock = 4
    MegaBomb = 5
    Hyperborean = 6
    Chameleon = 7


class ArmourPiece(IntFlag):
    """
    Armour pieces are represented as bits in a byte, with the following mapping:
    - Bit 0 (0x01): Chestplate
    - Bit 1 (0x02): Helmet
    - Bit 2 (0x04): Gloves
    - Bit 4 (0x10): Boots (any value with bit 4 set is considered to have boots equipped)
    """

    NONE = 0
    CHESTPLATE = 0x01
    HELMET = 0x02
    GLOVES = 0x04
    # Boots changes: it's any value with bit 4 set, because the game treats left and
    # right boots as one piece, so any value with bit 4 set is considered equipped.
    BOOTS = 0x10
    ALL = 0x17

    @classmethod
    def from_raw(cls, value: int) -> ArmourPiece:
        """Normalize raw value of armour piece because boots are represented by any value with bit 4 set"""
        normalized = value & 0x0F
        if value & _BOOTS_MASK:
            normalized |= cls.BOOTS
        return cls(normalized)


class ArmourSlot:
    """Descriptor for equiped armour slot"""

    def __init__(self, slot_name: str) -> None:
        self.slot_name = slot_name

    def _address(self, instance) -> int:
        return instance.base + instance._OFFSETS[self.slot_name]

    def __get__(self, instance, owner) -> ArmourSet | None:
        if instance is None:
            return None
        value = instance.pine.read_int8(self._address(instance))
        if value == 0:
            return None
        return ArmourSet(value)

    def __set__(self, instance, value) -> None:
        if instance is None:
            return
        instance.pine.write_int8(self._address(instance), value)

    def __delete__(self, instance) -> None:
        if instance is None:
            return
        instance.pine.write_int8(self._address(instance), 0)


class ArmourUnlockSlot:
    """Descriptor for unlocked armour slots"""

    def __init__(self, slot_name: str) -> None:
        self.slot_name = slot_name

    def _address(self, instance) -> int:
        return instance.base + instance._OFFSETS[self.slot_name]

    def __get__(self, instance, owner) -> ArmourPiece | None:
        if instance is None:
            return None
        value = instance.pine.read_int8(self._address(instance))
        return ArmourPiece.from_raw(value)

    def __set__(self, instance, value) -> None:
        if instance is None:
            return
        instance.pine.write_int8(self._address(instance), value)

    def __delete__(self, instance) -> None:
        if instance is None:
            return
        instance.pine.write_int8(self._address(instance), 0)


class EquippedArmour:
    _OFFSETS: dict[str, int] = {
        "chestplate": 0x00,
        "helmet": 0x01,
        "gloves_left": 0x02,
        "gloves_right": 0x03,
        "boots_left": 0x04,
        "boots_right": 0x05,
    }

    chestplate = ArmourSlot("chestplate")
    helmet = ArmourSlot("helmet")
    gloves_left = ArmourSlot("gloves_left")
    gloves_right = ArmourSlot("gloves_right")
    boots_left = ArmourSlot("boots_left")
    boots_right = ArmourSlot("boots_right")

    def __init__(self, base: int, pine: Pine) -> None:
        self.base = base
        self.pine = pine

    def to_dict(self) -> dict[str, int]:
        return {name: int(getattr(self, name) or 0) for name in EquippedArmour._OFFSETS}

    @classmethod
    def from_ap_data(cls, base: int, pine: Pine, data: dict[str, int]) -> EquippedArmour:
        """Build an EquippedArmour bound to (base, pine) and write an Archipelago data-storage dict into it."""
        equipped = cls(base, pine)
        for name in EquippedArmour._OFFSETS:
            if name in data:
                setattr(equipped, name, int(data[name]))
        return equipped

    def __repr__(self) -> str:
        return f"EquippedArmour({self.to_dict()})"


class ArmourUnlocks:
    _OFFSETS: dict[str, int] = {
        "wildfire": 0x06,
        "sludge": 0x07,
        "crystallix": 0x08,
        "electroshock": 0x09,
        "mega_bomb": 0x0A,
        "hyperborean": 0x0B,
        "chameleon": 0x0C,
    }

    wildfire = ArmourUnlockSlot("wildfire")
    sludge = ArmourUnlockSlot("sludge")
    crystallix = ArmourUnlockSlot("crystallix")
    electroshock = ArmourUnlockSlot("electroshock")
    mega_bomb = ArmourUnlockSlot("mega_bomb")
    hyperborean = ArmourUnlockSlot("hyperborean")
    chameleon = ArmourUnlockSlot("chameleon")

    def __init__(self, base: int, pine: Pine) -> None:
        self.base = base
        self.pine = pine

    def owned_mask(self) -> int:
        """Bitmask with one bit per armour set (bit i = ArmourUnlocks._OFFSETS order) that has any piece owned."""
        return sum(1 << i for i, name in enumerate(ArmourUnlocks._OFFSETS) if getattr(self, name))

    def to_dict(self) -> dict[str, int]:
        return {name: int(getattr(self, name)) for name in ArmourUnlocks._OFFSETS}

    @classmethod
    def from_ap_data(cls, base: int, pine: Pine, data: dict[str, int]) -> ArmourUnlocks:
        """Build an ArmourUnlocks bound to (base, pine) and write an Archipelago data-storage dict into it."""
        unlocks = cls(base, pine)
        for name in ArmourUnlocks._OFFSETS:
            if name in data:
                setattr(unlocks, name, ArmourPiece.from_raw(int(data[name])))
        return unlocks

    def __repr__(self) -> str:
        return f"ArmourUnlocks({self.to_dict()})"


class ArmourPickup(NamedTuple):
    """
    Data record for an armour pickup's information.
    This is used for monitoring and modifying armour pickups in the game.
    """

    set_key: str
    piece: ArmourPiece
    name: str
    planet: str


ARMOUR_SET_TO_KEY: dict[ArmourSet, str] = {
    ArmourSet.Wildfire: "wildfire",
    ArmourSet.Sludge: "sludge",
    ArmourSet.Crystallix: "crystallix",
    ArmourSet.Electroshock: "electroshock",
    ArmourSet.MegaBomb: "mega_bomb",
    ArmourSet.Hyperborean: "hyperborean",
    ArmourSet.Chameleon: "chameleon",
}

EQUIPPED_SLOT_TO_PIECE: dict[str, ArmourPiece] = {
    "chestplate": ArmourPiece.CHESTPLATE,
    "helmet": ArmourPiece.HELMET,
    "gloves_left": ArmourPiece.GLOVES,
    "gloves_right": ArmourPiece.GLOVES,
    "boots_left": ArmourPiece.BOOTS,
    "boots_right": ArmourPiece.BOOTS,
}

ARMOUR_PICKUPS: list[ArmourPickup] = [
    ArmourPickup("wildfire", ArmourPiece.CHESTPLATE, Rac5Locations.POKITARU_CHESTPLATE, Rac5Planets.POKITARU),
    ArmourPickup("wildfire", ArmourPiece.GLOVES, Rac5Locations.POKITARU_GLOVES, Rac5Planets.POKITARU),
    ArmourPickup("sludge", ArmourPiece.BOOTS, Rac5Locations.RYLLUS_BOOTS, Rac5Planets.RYLLUS),
    ArmourPickup("wildfire", ArmourPiece.HELMET, Rac5Locations.RYLLUS_HELMET, Rac5Planets.RYLLUS),
    ArmourPickup("sludge", ArmourPiece.CHESTPLATE, Rac5Locations.KALIDON_CHESTPLATE, Rac5Planets.KALIDON),
    ArmourPickup("wildfire", ArmourPiece.BOOTS, Rac5Locations.KALIDON_BOOTS, Rac5Planets.KALIDON),
    # ArmourPickup("electroshock", ArmourPiece.GLOVES, Rac5Locations.METALIS_GLOVES,
    #              Rac5Planets.METALIS),  # currently unreachable
    ArmourPickup("crystallix", ArmourPiece.CHESTPLATE, Rac5Locations.DREAMTIME_CHESTPLATE, Rac5Planets.DREAMTIME),
    ArmourPickup("crystallix", ArmourPiece.BOOTS, Rac5Locations.OUTPOST_OMEGA_BOOTS, Rac5Planets.OUTPOST_OMEGA),
    # ArmourPickup("electroshock", ArmourPiece.CHESTPLATE, "Challax: Electroshock Chestplate",
    #              Rac5Planets.CHALLAX),  # not reachable
    ArmourPickup("electroshock", ArmourPiece.HELMET, Rac5Locations.CHALLAX_HELMET, Rac5Planets.CHALLAX),
    ArmourPickup("mega_bomb", ArmourPiece.HELMET, Rac5Locations.DAYNI_MOON_HELMET, Rac5Planets.DAYNI_MOON),
    ArmourPickup("mega_bomb", ArmourPiece.CHESTPLATE, Rac5Locations.INSIDE_CLANK_CHESTPLATE, Rac5Planets.INSIDE_CLANK),
]

ARMOUR_FLAG_TO_LOCATION: dict[tuple[str, ArmourPiece], str] = {(ap.set_key, ap.piece): ap.name for ap in ARMOUR_PICKUPS}

CHALLENGE_LOCATION_TO_ARMOUR_FLAG: dict[str, tuple[str, ArmourPiece]] = {
    RACSMCLANK.METALIS_REVENGE: ("crystallix", ArmourPiece.HELMET),
    RACSMCLANK.METALIS_UBER: ("crystallix", ArmourPiece.GLOVES),
    RACSMCLANK.METALIS_NIGHT: ("sludge", ArmourPiece.GLOVES),
    RACSMCLANK.DAYNI_MOON_SHOWDOWN: ("mega_bomb", ArmourPiece.GLOVES),
    RACSMCLANK.DAYNI_MOON_INFINITE: ("mega_bomb", ArmourPiece.BOOTS),
    RACSMSKY.OUTPOST_OMEGA_VERTIGO: ("electroshock", ArmourPiece.BOOTS),
}


# Armour set checks


class ArmourInventory(BaseState):
    """Minimal replacement for ArmourState: holds EquipedArmour/UnlockedArmour
    (both pine-backed) and pushes both to Archipelago data storage. Change
    detection is external now (PlanetInventory.check_collected_armour() reads
    these live) — no accessor, no registered handlers.
    """

    def __init__(
        self,
        pine: Pine,
        base: int = ArmourStruct.BASE_ADDRESS,
    ) -> None:
        super().__init__()
        self.base = base
        self.pine = pine
        self.UnlockedArmour = ArmourUnlocks(base, pine)
        self.EquipedArmour = EquippedArmour(base, pine)
        self.on_equipped_save: Callable[[dict[str, int]], None] = lambda _: None
        self.on_unlocked_save: Callable[[dict[str, int]], None] = lambda _: None

    def set_unlocked_armour(self, state: ArmourUnlocks) -> None:
        """Save the current unlocked-sets values into UnlockedArmour."""
        self.UnlockedArmour = state

    def set_equipped_armour(self, state: EquippedArmour) -> None:
        """Save the current equipped-slot values into EquipedArmour."""
        self.EquipedArmour = state

    def sync_equipped(self, data: dict[str, int]) -> None:
        """Convert an Archipelago data-storage dict and write it into game memory as equipped slots."""
        self.set_equipped_armour(EquippedArmour.from_ap_data(self.base, self.pine, data))

    def sync_unlocked(self, data: dict[str, int]) -> None:
        """Convert an Archipelago data-storage dict and write it into game memory as unlocked sets."""
        self.set_unlocked_armour(ArmourUnlocks.from_ap_data(self.base, self.pine, data))

    def sync(self, equipped_data: dict[str, int], unlocked_data: dict[str, int]) -> None:
        """Convert Archipelago data-storage dicts and write both equipped slots and unlocked sets into game memory."""
        self.sync_equipped(equipped_data)
        self.sync_unlocked(unlocked_data)

    def push_equipped_armour(self) -> None:
        """Push the current equipped-slot values to Archipelago data storage."""
        self.on_equipped_save(self.EquipedArmour.to_dict())

    def push_unlocked_armour(self) -> None:
        """Push the current unlocked-sets values to Archipelago data storage."""
        self.on_unlocked_save(self.UnlockedArmour.to_dict())

    def __repr__(self) -> str:
        return f"ArmourInventory(equipped={self.EquipedArmour}, unlocked={self.UnlockedArmour})"


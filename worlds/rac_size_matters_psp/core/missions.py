from __future__ import annotations

from typing import TYPE_CHECKING

from .locations.mission_locations import PRESET_MISSION_BITS, VALIDATED_MISSION_MAP
from .address_maps import CURRENT_PLANET_ADDRESS

if TYPE_CHECKING:
    from ..pypsp import Psp

__all__ = [
    "VALIDATED_MISSION_MAP",
    "MissionInventory",
]


class MissionSlot:
    """Psp-backed accessor for a single mission-completion bit within a
    shared per-planet 2-byte mission value (several locations can share one
    planet's address, each owning a different mask bit)."""

    def __init__(self, address: int, mask: int) -> None:
        self.address = address
        self.mask = mask

    def __get__(self, instance, owner) -> bool | None:
        if instance is None:
            return None
        return bool(instance.pine.read_int16(self.address) & self.mask)

    def __set__(self, instance, value: bool) -> None:
        if instance is None:
            return
        raw = instance.pine.read_int16(self.address)
        raw = (raw | self.mask) if value else (raw & ~self.mask)
        instance.pine.write_int16(self.address, raw)

    def __delete__(self, instance) -> None:
        if instance is None:
            return
        raw = instance.pine.read_int16(self.address)
        instance.pine.write_int16(self.address, raw & ~self.mask)


class MissionInventory:
    """Psp-backed live accessor + completion tracking for story/cutscene
    missions, replacing MissionsState. Global fixed per-planet addresses."""

    def __init__(self, pine: Psp) -> None:
        self.pine = pine
        self._slots: dict[str, MissionSlot] = {
            name: MissionSlot(address, mask) for (address, mask), name in VALIDATED_MISSION_MAP.items()
        }
        self.completed: set[str] = set()

    def get(self, name: str) -> bool:
        return bool(self._slots[name].__get__(self, type(self)))

    def set(self, name: str, value: bool) -> None:
        self._slots[name].__set__(self, value)

    def delete(self, name: str) -> None:
        self._slots[name].__delete__(self)

    def setup(self) -> None:
        """OR the preset mission bits into memory so they never fire as location checks."""
        for addr, mask in PRESET_MISSION_BITS:
            raw = self.pine.read_int16(addr)
            self.pine.write_int16(addr, raw | mask)

    def check(self, planet_id: int | None = None) -> list[str]:
        """Only accept mission flags on their planet, as in the PS2 tracker.

        Outpost Omega's two overlays share its save word. Read each word once
        so checks backed by the same word see a consistent value this poll.
        """
        from ..locations import ALL_LOCATIONS

        if planet_id is None:
            planet_id = self.pine.read_int8(CURRENT_PLANET_ADDRESS)
        mission_planet = 6 if planet_id == 0x17 else planet_id
        raw_by_address: dict[int, int] = {}
        newly: list[str] = []
        for name, slot in self._slots.items():
            if name in self.completed:
                continue
            completion = ALL_LOCATIONS[name].completed
            if completion.planet_id is not None and completion.planet_id != mission_planet:
                continue
            if slot.address not in raw_by_address:
                raw_by_address[slot.address] = self.pine.read_int16(slot.address)
            if raw_by_address[slot.address] & slot.mask:
                self.completed.add(name)
                newly.append(name)
        return newly

    def sync(self) -> None:
        """Baseline read: populate completed without reporting anything as newly completed."""
        for name, slot in self._slots.items():
            if slot.__get__(self, type(self)):
                self.completed.add(name)

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        self.completed.update(name for name in checked_locations if name in VALIDATED_MISSION_MAP.values())

    def __repr__(self) -> str:
        return f"MissionInventory(completed={len(self.completed)}/{len(VALIDATED_MISSION_MAP)})"

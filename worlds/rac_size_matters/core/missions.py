from __future__ import annotations

from typing import TYPE_CHECKING

from .locations.mission_locations import PRESET_MISSION_BITS, VALIDATED_MISSION_MAP

if TYPE_CHECKING:
    from pypine import Pine

__all__ = [
    "VALIDATED_MISSION_MAP",
    "MissionInventory",
]


class MissionSlot:
    """Pine-backed accessor for a single mission-completion bit within a
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
    """Pine-backed live accessor + completion tracking for story/cutscene
    missions, replacing MissionsState. Global fixed per-planet addresses."""

    def __init__(self, pine: Pine) -> None:
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

    def check(self) -> list[str]:
        """Read every tracked bit and return newly completed AP location names for this call."""
        newly: list[str] = []
        for name, slot in self._slots.items():
            if name in self.completed:
                continue
            if slot.__get__(self, type(self)):
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

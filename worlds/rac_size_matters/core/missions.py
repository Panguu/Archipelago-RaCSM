from __future__ import annotations

from typing import TYPE_CHECKING

from .locations.mission_locations import LOCATION_TO_PLANET_ID, VALIDATED_MISSION_MAP

if TYPE_CHECKING:
    from ..pypine import Pine

__all__ = [
    "VALIDATED_MISSION_MAP",
    "MissionInventory",
]

# name -> (address, mask), the same data VALIDATED_MISSION_MAP holds the other way
# round.
_NAME_TO_ADDR_MASK: dict[str, tuple[int, int]] = {
    name: (address, mask) for (address, mask), name in VALIDATED_MISSION_MAP.items()
}

# Distinct addresses to batch-read each call — several location names can share one
# planet's address (each owning a different mask bit within it).
_ADDRESSES: tuple[int, ...] = tuple(sorted({address for address, _mask in _NAME_TO_ADDR_MASK.values()}))


class MissionInventory:
    """Pine-backed live accessor + completion tracking for story/cutscene missions.
    check() refuses to report a location as newly completed unless the player is
    currently on its planet — else a stray bit could fire while on an unrelated planet."""

    def __init__(self, pine: Pine) -> None:
        self.pine = pine
        self.completed: set[str] = set()

    def _read_all(self) -> dict[int, int]:
        values = self.pine.batch_read_int16(list(_ADDRESSES))
        return dict(zip(_ADDRESSES, values, strict=True))

    def get(self, name: str) -> bool:
        address, mask = _NAME_TO_ADDR_MASK[name]
        return bool(self.pine.read_int16(address) & mask)

    def set(self, name: str, value: bool) -> None:
        address, mask = _NAME_TO_ADDR_MASK[name]
        raw = self.pine.read_int16(address)
        raw = (raw | mask) if value else (raw & ~mask)
        self.pine.write_int16(address, raw)

    def delete(self, name: str) -> None:
        self.set(name, False)

    def check(self, planet_id: int | None) -> list[str]:
        """Read every tracked bit and return newly completed AP location names. A location
        tied to a planet is only accepted while `planet_id` matches, else left unmarked."""
        raw_by_address = self._read_all()
        newly: list[str] = []
        for name, (address, mask) in _NAME_TO_ADDR_MASK.items():
            if name in self.completed:
                continue
            if not (raw_by_address[address] & mask):
                continue
            required_planet = LOCATION_TO_PLANET_ID.get(name)
            if required_planet is not None and planet_id != required_planet:
                continue
            self.completed.add(name)
            newly.append(name)
        return newly

    def sync(self) -> None:
        """Baseline read: populate completed without reporting anything as newly
        completed, and without the planet gate — a reconnect trusts whatever's in memory."""
        raw_by_address = self._read_all()
        for name, (address, mask) in _NAME_TO_ADDR_MASK.items():
            if raw_by_address[address] & mask:
                self.completed.add(name)

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        self.completed.update(name for name in checked_locations if name in VALIDATED_MISSION_MAP.values())

    def __repr__(self) -> str:
        return f"MissionInventory(completed={len(self.completed)}/{len(VALIDATED_MISSION_MAP)})"

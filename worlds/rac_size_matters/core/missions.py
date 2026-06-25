from __future__ import annotations

import struct
from collections.abc import Callable

from CommonClient import logger

from ..constants import Rac5CutsceneLocations
from ..interface_orchestrator.memory.accessor import MemoryAccessor
from ..interface_orchestrator.state.base_state import BaseState
from ..interface_orchestrator.storage.local import LocalStorage
from ..interface_orchestrator.structs.address_map import AddressMap
from .address_maps import PLANET_MISSION_ADDRESSES, PLANET_MISSION_ADDRESSES as _ADDRS
from .structs.game import MissionsStruct

# Maps (address, mask) -> location_name.
# Detection: (current_value & mask) != 0
# mask of 0x0000 means not yet validated — skipped by MissionsState.

# Bits that must be force-written on initial load (not location checks).
PRESET_MISSION_BITS: list[tuple[int, int]] = [
    (_ADDRS["Pokitaru"], 0x0004),   # Rescue the girl
    (_ADDRS["Kalidon"],  0x0004),   # Search the factory
    (_ADDRS["Challax"],  0x0004),   # Explore the miniature city
]

# Story missions
STORY_MISSION_MAP: dict[tuple[int, int], str] = {
    # Pokitaru
    (_ADDRS["Pokitaru"],      0x0002): Rac5CutsceneLocations.POKITARU_FIGHT,

    # Ryllus
    (_ADDRS["Ryllus"],        0x0008): Rac5CutsceneLocations.RYLLUS_ARTIFACT,
    (_ADDRS["Ryllus"],        0x0010): Rac5CutsceneLocations.RYLLUS_TEMPLE,

    # Kalidon
    (_ADDRS["Kalidon"],       0x0010): Rac5CutsceneLocations.KALIDON_WIN,

    # Metalis
    (_ADDRS["Metalis"],       0x0002): Rac5CutsceneLocations.METALIS_WAR,
    # (_ADDRS["Metalis"],     0x0004): Rac5CutsceneLocations.METALIS_ESCAPE,  # Giant Clank disabled — unreachable

    # Dreamtime
    (_ADDRS["Dreamtime"],     0x0004): Rac5CutsceneLocations.DREAMTIME_COMPLETE,

    # Outpost Omega
    (_ADDRS["Outpost Omega"], 0x0080): Rac5CutsceneLocations.OUTPOST_OMEGA_ESCAPE,
    (_ADDRS["Outpost Omega"], 0x0010): Rac5CutsceneLocations.OUTPOST_OMEGA_REMATCH,

    # Challax
    # (_ADDRS["Challax"],     0x0020): Rac5CutsceneLocations.CHALLAX_CLANK,  # Giant Clank disabled — unreachable

    # Dayni Moon
    (_ADDRS["Dayni Moon"],    0x0008): Rac5CutsceneLocations.DAYNI_MOON,
    (_ADDRS["Dayni Moon"],    0x0004): Rac5CutsceneLocations.DAYNI_MOON_LUNA,
    (_ADDRS["Dayni Moon"],    0x0020): Rac5CutsceneLocations.INSIDE_CLANK_ESCAPE,

    # Inside Clank
    (_ADDRS["Inside Clank"],  0x0002): Rac5CutsceneLocations.INSIDE_CLANK_TECHNOMITES,

    # Quodrona
    (_ADDRS["Quodrona"],      0x0004): Rac5CutsceneLocations.QUODRONA_FIND,
    (_ADDRS["Quodrona"],      0x0140): Rac5CutsceneLocations.QUODRONA_GOAL,
}

# Cutscenes
CUTSCENE_MAP: dict[tuple[int, int], str] = {
    # Enter Planet (mask 0x0001 on each planet's mission address)
    (_ADDRS["Pokitaru"],      0x0001): Rac5CutsceneLocations.POKITARU_ENTER,
    (_ADDRS["Ryllus"],        0x0001): Rac5CutsceneLocations.RYLLUS_ENTER,
    (_ADDRS["Kalidon"],       0x0001): Rac5CutsceneLocations.KALIDON_ENTER,
    (_ADDRS["Metalis"],       0x0001): Rac5CutsceneLocations.METALIS_ENTER,
    (_ADDRS["Dreamtime"],     0x0001): Rac5CutsceneLocations.DREAMTIME_ENTER,
    (_ADDRS["Outpost Omega"], 0x0001): Rac5CutsceneLocations.OUTPOST_OMEGA_ENTER,
    (_ADDRS["Challax"],       0x0001): Rac5CutsceneLocations.CHALLAX_ENTER,
    (_ADDRS["Dayni Moon"],    0x0001): Rac5CutsceneLocations.DAYNI_MOON_ENTER,
    (_ADDRS["Inside Clank"],  0x0001): Rac5CutsceneLocations.INSIDE_CLANK_ENTER,
    (_ADDRS["Quodrona"],      0x0001): Rac5CutsceneLocations.QUODRONA_ENTER,

    # Flag-triggered events
    (_ADDRS["Ryllus"],        0x0002): Rac5CutsceneLocations.RYLLUS_BUZZING,
    (_ADDRS["Kalidon"],       0x0008): Rac5CutsceneLocations.KALIDON_EXPLORE,
    (_ADDRS["Outpost Omega"], 0x0002): Rac5CutsceneLocations.OUTPOST_OMEGA,
    # (_ADDRS["Challax"],     0x0010): Rac5CutsceneLocations.METALIS_CLANK,  # Giant Clank disabled — unreachable
    (_ADDRS["Dayni Moon"],    0x0010): Rac5CutsceneLocations.DAYNI_MOON_FIGHT1,
    (_ADDRS["Dayni Moon"],    0x0002): Rac5CutsceneLocations.DAYNI_MOON_FIGHT2,
    (_ADDRS["Quodrona"],      0x0008): Rac5CutsceneLocations.QUODRONA_CLONE,
    (_ADDRS["Quodrona"],      0x0010): Rac5CutsceneLocations.QUODRONA_CHASE,
    (_ADDRS["Quodrona"],      0x0020): Rac5CutsceneLocations.QUODRONA_MECHA,
}

# Combined (used by MissionsState to watch all possible completions)
MISSION_COMPLETE_MAP: dict[tuple[int, int], str] = {**STORY_MISSION_MAP, **CUTSCENE_MAP}

VALIDATED_MISSION_MAP: dict[tuple[int, int], str] = {
    k: v for k, v in MISSION_COMPLETE_MAP.items() if k[1] != 0x0000
}


# State (runtime)

# Reverse map: address -> planet name for log messages
_PLANET_BY_ADDR: dict[int, str] = {v: k for k, v in PLANET_MISSION_ADDRESSES.items()}


class MissionsState(BaseState):
    """Watches the per-planet 2-byte mission progress values, logs any raw value
    change, and fires a callback when a known mission's complete value is reached."""

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self._completed: set[str]                        = set()
        self._snapshots: dict[int, int]                  = {}   # addr -> last seen value
        self._on_mission_complete: Callable[[str], None] = lambda _: None

    def set_mission_complete_callback(self, cb: Callable[[str], None]) -> None:
        self._on_mission_complete = cb

    def on_exit(self) -> None:
        self._on_mission_complete = lambda _: None

    def _register_handlers(self) -> None:
        self.accessor.on_struct_change(MissionsStruct, self._on_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(MissionsStruct, self._on_change)

    def _on_change(self, address: int, new_bytes: bytes) -> None:
        del address, new_bytes
        for addr, planet in _PLANET_BY_ADDR.items():
            raw = self.accessor.read_raw(addr, 2)
            if not raw or len(raw) < 2:
                continue
            value = struct.unpack_from("<H", raw)[0]
            prev  = self._snapshots.get(addr)
            if prev is not None and value != prev:
                logger.debug(
                    f"[RAC] Mission change  {planet:<16}  {addr:#010x}  "
                    f"{prev:#06x} -> {value:#06x}  (XOR {value ^ prev:#06x})"
                )
            self._snapshots[addr] = value

        self._check_all()

    def _check_all(self) -> None:
        for (addr, mask), name in VALIDATED_MISSION_MAP.items():
            if name in self._completed:
                continue
            raw = self.accessor.read_raw(addr, 2)
            if not raw or len(raw) < 2:
                continue
            value = struct.unpack_from("<H", raw)[0]
            if value & mask:
                self._completed.add(name)
                self._on_mission_complete(name)

    def preset_missions(self) -> None:
        """OR preset bits into memory and mark them done so they never fire as checks."""
        for addr, mask in PRESET_MISSION_BITS:
            raw = self.accessor.read_raw(addr, 2)
            if not raw or len(raw) < 2:
                continue
            value = struct.unpack_from("<H", raw)[0]
            self.accessor.write_raw(addr, struct.pack("<H", value | mask))

    def sync(self) -> None:
        for addr in _PLANET_BY_ADDR:
            raw = self.accessor.read_raw(addr, 2)
            if raw and len(raw) >= 2:
                self._snapshots[addr] = struct.unpack_from("<H", raw)[0]
        self._check_all()

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        self._completed.update(
            name for name in checked_locations
            if name in VALIDATED_MISSION_MAP.values()
        )

    def __repr__(self) -> str:
        total = len(VALIDATED_MISSION_MAP)
        return f"MissionsState(completed={len(self._completed)}/{total})"

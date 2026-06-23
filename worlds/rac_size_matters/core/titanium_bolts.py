from __future__ import annotations

from dataclasses import dataclass

from ..constants import RACSMPLANET, RACSMTBOLT
from ..interface_orchestrator.memory.accessor import MemoryAccessor
from ..interface_orchestrator.state.base_state import BaseState
from ..interface_orchestrator.storage.local import LocalStorage
from ..interface_orchestrator.structs.address_map import AddressMap
from .structs.pickups import TitaniumBoltStruct

__all__ = [
    "TitaniumBolt",
    "TitaniumBoltAddresses",
    "TITANIUM_BOLTS",
    "BOLT_BY_PLANET_AND_DELTA",
    "TitaniumBoltState",
]


# ── Address resolver ─────────────────────────────────────────────────────────────

class TitaniumBoltAddresses:
    """Resolves titanium bolt field addresses from a single base address.

    Layout (identical on PSP and PS2):
      +0x00  pickup  — increments each time a bolt is picked up
      +0x05  total   — cumulative bolt count
    """

    def __init__(self, base: int) -> None:
        self.base   = base
        self.pickup = base + 0x00
        self.total  = base + 0x05


# ── Data ────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TitaniumBolt:
    planet_id: int  # used with delta for unambiguous detection
    bit:       int  # bit position in the pickup int64
    region:    str  # AP region name

    @property
    def delta(self) -> int:
        return 1 << self.bit


TITANIUM_BOLTS: dict[str, TitaniumBolt] = {
    RACSMTBOLT.POKITARU_ZIPLINE:   TitaniumBolt(0x01,  0, RACSMPLANET.POKITARU),
    RACSMTBOLT.POKITARU_HUT:       TitaniumBolt(0x01,  1, RACSMPLANET.POKITARU),
    RACSMTBOLT.RYLLUS_CLIFF:       TitaniumBolt(0x02,  4, RACSMPLANET.RYLLUS),
    RACSMTBOLT.RYLLUS_WALL:        TitaniumBolt(0x02,  5, RACSMPLANET.RYLLUS),
    RACSMTBOLT.KALIDON_SHIP:       TitaniumBolt(0x03,  8, RACSMPLANET.KALIDON),
    RACSMTBOLT.KALIDON_FACTORY:    TitaniumBolt(0x03, 10, RACSMPLANET.KALIDON),
    RACSMTBOLT.KALIDON_RAMP:       TitaniumBolt(0x03,  9, RACSMPLANET.KALIDON),
    RACSMTBOLT.METALIS_DOOR:       TitaniumBolt(0x04, 12, RACSMPLANET.METALIS),
    RACSMTBOLT.DREAMTIME_HAT:      TitaniumBolt(0x05, 16, RACSMPLANET.DREAMTIME),
    RACSMTBOLT.DREAMTIME_GARAGE:   TitaniumBolt(0x05, 17, RACSMPLANET.DREAMTIME),
    RACSMTBOLT.DREAMTIME_CRAB:     TitaniumBolt(0x05, 18, RACSMPLANET.DREAMTIME),
    RACSMTBOLT.OUTPOST_OMEGA_DREAM:TitaniumBolt(0x17, 20, RACSMPLANET.OUTPOST_OMEGA),
    RACSMTBOLT.CHALLAX_MECH_PAD:   TitaniumBolt(0x07, 24, RACSMPLANET.CHALLAX),
    RACSMTBOLT.CHALLAX_ROOM:       TitaniumBolt(0x07, 25, RACSMPLANET.CHALLAX),
    RACSMTBOLT.CHALLAX_PLANT:      TitaniumBolt(0x07, 26, RACSMPLANET.CHALLAX),
    RACSMTBOLT.DAYNI_MOON_BARN:    TitaniumBolt(0x08, 28, RACSMPLANET.DAYNI_MOON),
    RACSMTBOLT.DAYNI_MOON_MIMIC:   TitaniumBolt(0x08, 29, RACSMPLANET.DAYNI_MOON),
    RACSMTBOLT.INSIDE_CLANK_LADDER:TitaniumBolt(0x09, 32, RACSMPLANET.INSIDE_CLANK),
    RACSMTBOLT.INSIDE_CLANK_WALL:  TitaniumBolt(0x09, 33, RACSMPLANET.INSIDE_CLANK),
    RACSMTBOLT.QUODRONA_DUMMIES:   TitaniumBolt(0x0A, 36, RACSMPLANET.QUODRONA),
}

# (planet_id, delta) → location name — used by the client for unambiguous detection
BOLT_BY_PLANET_AND_DELTA: dict[tuple[int, int], str] = {
    (bolt.planet_id, bolt.delta): name
    for name, bolt in TITANIUM_BOLTS.items()
}


# ── State (runtime) ──────────────────────────────────────────────────────────────

class TitaniumBoltState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self._poll_last:   int = 0
        self._synced_mask: int = 0

    def _register_handlers(self) -> None:
        self.accessor.on_struct_change(TitaniumBoltStruct, self._on_struct_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(TitaniumBoltStruct, self._on_struct_change)

    def _on_struct_change(self, address: int, new_bytes: bytes) -> None:
        del address
        current = int.from_bytes(new_bytes[:5], "little")
        delta   = current - self._poll_last
        self._poll_last = current
        if delta > 0 and (delta & (delta - 1)) == 0:
            self.on_bolt_delta(delta)

    def sync(self) -> None:
        raw     = self.accessor.read_raw(TitaniumBoltStruct.BASE_ADDRESS, 5)
        current = int.from_bytes(raw, "little") if raw else 0
        self._poll_last = current
        new_val = current | self._synced_mask
        if new_val != current:
            self.accessor.write_raw(TitaniumBoltStruct.BASE_ADDRESS, new_val.to_bytes(5, "little"))

    def sync_from_ap(self, checked_location_names: set[str]) -> None:
        mask = 0
        for loc_name, bolt in TITANIUM_BOLTS.items():
            if loc_name in checked_location_names:
                mask |= bolt.delta
        self._synced_mask = mask

    def on_bolt_delta(self, _delta: int) -> None:
        del _delta

    def __repr__(self) -> str:
        collected = bin(self._poll_last).count("1")
        return f"TitaniumBoltState(collected={collected}/{len(TITANIUM_BOLTS)})"

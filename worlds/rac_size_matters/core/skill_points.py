from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from ..constants import Rac5Planets, Rac5SkillPoints
from ..interface_orchestrator.memory.accessor import MemoryAccessor
from ..interface_orchestrator.state.base_state import BaseState
from ..interface_orchestrator.storage.local import LocalStorage
from ..interface_orchestrator.structs.address_map import AddressMap
from .address_maps import SKILL_POINTS_BASE as SKILL_POINT_ADDRESS
from .structs.pickups import SkillPointsStruct

logger = logging.getLogger("Client")

__all__ = [
    "SkillPoint",
    "SKILL_POINTS",
    "HARD_SKILL_POINTS",
    "CLANK_CHALLENGE_SKILL_POINTS",
    "SKYBOARD_CHALLENGE_SKILL_POINTS",
    "SKILL_POINT_BY_PLANET_AND_MASK",
    "LOCATION_SKILL_POINTS",
    "SKILL_POINT_ADDRESS",
    "SkillPointState",
]


# â”€â”€ Data â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@dataclass(frozen=True)
class SkillPoint:
    planet_id: int  # used with mask for detection context
    bit:       int
    region:    str

    @property
    def mask(self) -> int:
        return 1 << self.bit


# Confirmed bit layout (groups of 2-3, 4-bit spacing between planets):
#
#  Planet        Count  Bits
#  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
#  Pokitaru        3     0,  1,  2
#  Ryllus          3     4,  5,  6
#  Kalidon         3     8,  9, 10
#  Metalis         3    12, 13, 14
#  Dreamtime       2    16, 17
#  Outpost Omega   1    20
#  Challax         3    24, 25, 26
#  Dayni Moon      3    28, 29, 30
#  Inside Clank    2    32, 33
#  Quodrona        2    36, 37

SKILL_POINTS: dict[str, SkillPoint] = {
    # Pokitaru
    Rac5SkillPoints.POKITARU_TRAIN:          SkillPoint(0x01,  0, Rac5Planets.POKITARU),
    Rac5SkillPoints.POKITARU_BOAT:           SkillPoint(0x01,  1, Rac5Planets.POKITARU),
    Rac5SkillPoints.POKITARU_COWS:           SkillPoint(0x01,  2, Rac5Planets.POKITARU),
    # Ryllus
    Rac5SkillPoints.RYLLUS_BURY:             SkillPoint(0x02,  4, Rac5Planets.RYLLUS),
    Rac5SkillPoints.RYLLUS_CAMERA:           SkillPoint(0x02,  5, Rac5Planets.RYLLUS),
    Rac5SkillPoints.RYLLUS_SHIP_IT:          SkillPoint(0x02,  6, Rac5Planets.RYLLUS),
    # Kalidon
    Rac5SkillPoints.KALIDON_EXPLOSIVE:       SkillPoint(0x03,  8, Rac5Planets.KALIDON),
    Rac5SkillPoints.KALIDON_SUPER_LOMBAX:    SkillPoint(0x03,  9, Rac5Planets.KALIDON),
    Rac5SkillPoints.KALIDON_SKYBOARDER:      SkillPoint(0x03, 10, Rac5Planets.KALIDON),
    # Metalis
    Rac5SkillPoints.METALIS_SHUTOUT:         SkillPoint(0x04, 12, Rac5Planets.METALIS),
    # Rac5SkillPoints.METALIS_TERROR: SkillPoint(0x04, 13, Rac5Planets.METALIS)
    # Giant Clank disabled â€” unreachable.
    Rac5SkillPoints.METALIS_GLADIATOR:       SkillPoint(0x04, 14, Rac5Planets.METALIS),
    # Dreamtime
    Rac5SkillPoints.DREAMTIME_FRIENDS:       SkillPoint(0x05, 16, Rac5Planets.DREAMTIME),
    Rac5SkillPoints.DREAMTIME_NIGHT_TERRORS: SkillPoint(0x05, 17, Rac5Planets.DREAMTIME),
    # Outpost Omega
    Rac5SkillPoints.OUTPOST_OMEGA_AWESOME:   SkillPoint(0x17, 20, Rac5Planets.OUTPOST_OMEGA),
    # Challax
    # Rac5SkillPoints.CHALLAX_SHOCK: SkillPoint(0x07, 24, Rac5Planets.CHALLAX)
    # Excluded: only one opportunity to complete this in the whole game (bit 24).
    Rac5SkillPoints.CHALLAX_MASTER:          SkillPoint(0x07, 25, Rac5Planets.CHALLAX),
    Rac5SkillPoints.CHALLAX_VARMINTS:        SkillPoint(0x07, 26, Rac5Planets.CHALLAX),
    # Dayni Moon
    Rac5SkillPoints.DAYNI_MOON_GLADIATOR:    SkillPoint(0x08, 28, Rac5Planets.DAYNI_MOON),
    Rac5SkillPoints.DAYNI_MOON_WOOL_PROTEST: SkillPoint(0x08, 29, Rac5Planets.DAYNI_MOON),
    Rac5SkillPoints.DAYNI_MOON_BOUNCY:       SkillPoint(0x08, 30, Rac5Planets.DAYNI_MOON),
    # Inside Clank
    Rac5SkillPoints.INSIDE_CLANK_SHOCK:      SkillPoint(0x09, 32, Rac5Planets.INSIDE_CLANK),
    Rac5SkillPoints.INSIDE_CLANK_RATCHET:    SkillPoint(0x09, 33, Rac5Planets.INSIDE_CLANK),
    # Quodrona
    Rac5SkillPoints.QUODRONA_ELITE:          SkillPoint(0x0A, 36, Rac5Planets.QUODRONA),
    Rac5SkillPoints.QUODRONA_STORM:          SkillPoint(0x0A, 37, Rac5Planets.QUODRONA),
}

# Curated "hard" tier for the Skill Points option. Everything else in SKILL_POINTS
# that isn't also a Clank/Skyboard challenge skill point counts as "easy".
HARD_SKILL_POINTS: frozenset[str] = frozenset({
    Rac5SkillPoints.RYLLUS_BURY,
    Rac5SkillPoints.KALIDON_SUPER_LOMBAX,
    # Rac5SkillPoints.METALIS_TERROR,  # Giant Clank disabled â€” unreachable
    Rac5SkillPoints.DREAMTIME_FRIENDS,
    Rac5SkillPoints.DREAMTIME_NIGHT_TERRORS,
    Rac5SkillPoints.CHALLAX_MASTER,
    Rac5SkillPoints.DAYNI_MOON_WOOL_PROTEST,
    Rac5SkillPoints.INSIDE_CLANK_SHOCK,
    Rac5SkillPoints.INSIDE_CLANK_RATCHET,
    Rac5SkillPoints.QUODRONA_ELITE,
    Rac5SkillPoints.QUODRONA_STORM,
})

# Earned from Clank Challenge arenas â€” gated by enable_clank_challenge_skill_points,
# independent of the Skill Points easy/hard tier.
CLANK_CHALLENGE_SKILL_POINTS: frozenset[str] = frozenset({
    Rac5SkillPoints.METALIS_SHUTOUT,
    Rac5SkillPoints.METALIS_GLADIATOR,
    Rac5SkillPoints.DAYNI_MOON_GLADIATOR,
})

# Earned from Skyboard Challenges â€” gated by enable_skyboard_challenge_skill_points,
# independent of the Skill Points easy/hard tier.
SKYBOARD_CHALLENGE_SKILL_POINTS: frozenset[str] = frozenset({
    Rac5SkillPoints.KALIDON_SKYBOARDER,
    Rac5SkillPoints.OUTPOST_OMEGA_AWESOME,
})

# (planet_id, mask) â†’ location name â€” mirrors BOLT_BY_PLANET_AND_DELTA
SKILL_POINT_BY_PLANET_AND_MASK: dict[tuple[int, int], str] = {
    (sp.planet_id, sp.mask): name
    for name, sp in SKILL_POINTS.items()
}

# Flat mask lookup used by the client (bits are globally unique so planet not needed for detection)
LOCATION_SKILL_POINTS: dict[str, int] = {
    name: sp.mask for name, sp in SKILL_POINTS.items()
}


# â”€â”€ State (runtime) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class SkillPointState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
        log: Callable[..., None] | None = None,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self._bits:          int  = 0
        self._synced_mask:   int  = 0
        self._planet_loaded: bool = False
        self._enabled:       bool = False
        self._log = log or logger.info

    def set_enabled(self, enabled: bool, planet_loaded: bool = False) -> None:
        was_enabled = self._enabled
        self._enabled = enabled
        if enabled:
            # Always remove then re-add to avoid duplicates on reconnect.
            self.accessor.remove_struct_handler(SkillPointsStruct, self._on_struct_change)
            # Baseline _bits BEFORE registering the handler â€” the poller runs on
            # a background thread and could otherwise fire _on_struct_change with
            # a stale (zero) baseline in the gap, treating every already-set bit
            # as "newly earned" and firing bogus location checks on connect.
            self._read_bits()
            if planet_loaded:
                self._planet_loaded = True
            self.accessor.on_struct_change(SkillPointsStruct, self._on_struct_change)
        elif was_enabled:
            self.accessor.remove_struct_handler(SkillPointsStruct, self._on_struct_change)

    def mark_planet_loaded(self) -> None:
        self._planet_loaded = True

    def _register_handlers(self) -> None:
        # Re-register after interface swap if already enabled.
        if self._enabled:
            self.accessor.on_struct_change(SkillPointsStruct, self._on_struct_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(SkillPointsStruct, self._on_struct_change)

    def _on_struct_change(self, address: int, new_bytes: bytes) -> None:
        del address
        instance  = SkillPointsStruct.from_bytes(new_bytes)
        current   = instance.bitmask
        newly_set = current & ~self._bits
        prev      = self._bits
        self._bits = current
        if not self._planet_loaded:
            return
        if newly_set:
            self._log(
                f"[RAC] Skill point bits: {prev:#010x} -> {current:#010x}  (earned: {newly_set:#010x})"
            )
            for name, sp in SKILL_POINTS.items():
                if newly_set & sp.mask:
                    self._log(f"[RAC] Skill point earned: {name}")
                    self.on_skill_point_earned(name)

    def _read_bits(self) -> None:
        try:
            instance = self.accessor.read_struct(SkillPointsStruct)
            self._bits = instance.bitmask
        except Exception:
            pass

    def sync(self) -> None:
        if not self._enabled:
            return
        instance = self.accessor.read_struct(SkillPointsStruct)
        self._bits = instance.bitmask
        self.mark_planet_loaded()
        new_val = instance.bitmask | self._synced_mask
        if new_val != instance.bitmask:
            instance.bitmask = new_val
            self.accessor.write_struct(instance)

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        mask = 0
        for name, sp in SKILL_POINTS.items():
            if name in checked_locations:
                mask |= sp.mask
        self._synced_mask = mask

    def on_skill_point_earned(self, _name: str) -> None:
        del _name

    def __repr__(self) -> str:
        earned = bin(self._bits).count("1")
        return f"SkillPointState(earned={earned}/{len(SKILL_POINTS)})"

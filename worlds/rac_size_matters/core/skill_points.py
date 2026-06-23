from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from ..constants import RACSMPLANET, RACSMSKILLPOINT
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


# ── Data ────────────────────────────────────────────────────────────────────────

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
#  ──────────────────────────
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
    RACSMSKILLPOINT.POKITARU_TRAIN:          SkillPoint(0x01,  0, RACSMPLANET.POKITARU),
    RACSMSKILLPOINT.POKITARU_BOAT:           SkillPoint(0x01,  1, RACSMPLANET.POKITARU),
    RACSMSKILLPOINT.POKITARU_COWS:           SkillPoint(0x01,  2, RACSMPLANET.POKITARU),
    # Ryllus
    RACSMSKILLPOINT.RYLLUS_BURY:             SkillPoint(0x02,  4, RACSMPLANET.RYLLUS),
    RACSMSKILLPOINT.RYLLUS_CAMERA:           SkillPoint(0x02,  5, RACSMPLANET.RYLLUS),
    RACSMSKILLPOINT.RYLLUS_SHIP_IT:          SkillPoint(0x02,  6, RACSMPLANET.RYLLUS),
    # Kalidon
    RACSMSKILLPOINT.KALIDON_EXPLOSIVE:       SkillPoint(0x03,  8, RACSMPLANET.KALIDON),
    RACSMSKILLPOINT.KALIDON_SUPER_LOMBAX:    SkillPoint(0x03,  9, RACSMPLANET.KALIDON),
    RACSMSKILLPOINT.KALIDON_SKYBOARDER:      SkillPoint(0x03, 10, RACSMPLANET.KALIDON),
    # Metalis
    RACSMSKILLPOINT.METALIS_SHUTOUT:         SkillPoint(0x04, 12, RACSMPLANET.METALIS),
    # RACSMSKILLPOINT.METALIS_TERROR: SkillPoint(0x04, 13, RACSMPLANET.METALIS)
    # Giant Clank disabled — unreachable.
    RACSMSKILLPOINT.METALIS_GLADIATOR:       SkillPoint(0x04, 14, RACSMPLANET.METALIS),
    # Dreamtime
    RACSMSKILLPOINT.DREAMTIME_FRIENDS:       SkillPoint(0x05, 16, RACSMPLANET.DREAMTIME),
    RACSMSKILLPOINT.DREAMTIME_NIGHT_TERRORS: SkillPoint(0x05, 17, RACSMPLANET.DREAMTIME),
    # Outpost Omega
    RACSMSKILLPOINT.OUTPOST_OMEGA_AWESOME:   SkillPoint(0x17, 20, RACSMPLANET.OUTPOST_OMEGA),
    # Challax
    # RACSMSKILLPOINT.CHALLAX_SHOCK: SkillPoint(0x07, 24, RACSMPLANET.CHALLAX)
    # Excluded: only one opportunity to complete this in the whole game (bit 24).
    RACSMSKILLPOINT.CHALLAX_MASTER:          SkillPoint(0x07, 25, RACSMPLANET.CHALLAX),
    RACSMSKILLPOINT.CHALLAX_VARMINTS:        SkillPoint(0x07, 26, RACSMPLANET.CHALLAX),
    # Dayni Moon
    RACSMSKILLPOINT.DAYNI_MOON_GLADIATOR:    SkillPoint(0x08, 28, RACSMPLANET.DAYNI_MOON),
    RACSMSKILLPOINT.DAYNI_MOON_WOOL_PROTEST: SkillPoint(0x08, 29, RACSMPLANET.DAYNI_MOON),
    RACSMSKILLPOINT.DAYNI_MOON_BOUNCY:       SkillPoint(0x08, 30, RACSMPLANET.DAYNI_MOON),
    # Inside Clank
    RACSMSKILLPOINT.INSIDE_CLANK_SHOCK:      SkillPoint(0x09, 32, RACSMPLANET.INSIDE_CLANK),
    RACSMSKILLPOINT.INSIDE_CLANK_RATCHET:    SkillPoint(0x09, 33, RACSMPLANET.INSIDE_CLANK),
    # Quodrona
    RACSMSKILLPOINT.QUODRONA_ELITE:          SkillPoint(0x0A, 36, RACSMPLANET.QUODRONA),
    RACSMSKILLPOINT.QUODRONA_STORM:          SkillPoint(0x0A, 37, RACSMPLANET.QUODRONA),
}

# Curated "hard" tier for the Skill Points option. Everything else in SKILL_POINTS
# that isn't also a Clank/Skyboard challenge skill point counts as "easy".
HARD_SKILL_POINTS: frozenset[str] = frozenset({
    RACSMSKILLPOINT.RYLLUS_BURY,
    RACSMSKILLPOINT.KALIDON_SUPER_LOMBAX,
    # RACSMSKILLPOINT.METALIS_TERROR,  # Giant Clank disabled — unreachable
    RACSMSKILLPOINT.DREAMTIME_FRIENDS,
    RACSMSKILLPOINT.DREAMTIME_NIGHT_TERRORS,
    RACSMSKILLPOINT.CHALLAX_MASTER,
    RACSMSKILLPOINT.DAYNI_MOON_WOOL_PROTEST,
    RACSMSKILLPOINT.INSIDE_CLANK_SHOCK,
    RACSMSKILLPOINT.INSIDE_CLANK_RATCHET,
    RACSMSKILLPOINT.QUODRONA_ELITE,
    RACSMSKILLPOINT.QUODRONA_STORM,
})

# Earned from Clank Challenge arenas — gated by enable_clank_challenge_skill_points,
# independent of the Skill Points easy/hard tier.
CLANK_CHALLENGE_SKILL_POINTS: frozenset[str] = frozenset({
    RACSMSKILLPOINT.METALIS_SHUTOUT,
    RACSMSKILLPOINT.METALIS_GLADIATOR,
    RACSMSKILLPOINT.DAYNI_MOON_GLADIATOR,
})

# Earned from Skyboard Challenges — gated by enable_skyboard_challenge_skill_points,
# independent of the Skill Points easy/hard tier.
SKYBOARD_CHALLENGE_SKILL_POINTS: frozenset[str] = frozenset({
    RACSMSKILLPOINT.KALIDON_SKYBOARDER,
    RACSMSKILLPOINT.OUTPOST_OMEGA_AWESOME,
})

# (planet_id, mask) → location name — mirrors BOLT_BY_PLANET_AND_DELTA
SKILL_POINT_BY_PLANET_AND_MASK: dict[tuple[int, int], str] = {
    (sp.planet_id, sp.mask): name
    for name, sp in SKILL_POINTS.items()
}

# Flat mask lookup used by the client (bits are globally unique so planet not needed for detection)
LOCATION_SKILL_POINTS: dict[str, int] = {
    name: sp.mask for name, sp in SKILL_POINTS.items()
}


# ── State (runtime) ──────────────────────────────────────────────────────────────

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
            # Baseline _bits BEFORE registering the handler — the poller runs on
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

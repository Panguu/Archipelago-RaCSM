from __future__ import annotations

from collections.abc import Callable
from enum import IntFlag
from typing import NamedTuple

from ..constants import (
    Rac5ClankChallenges as RACSMCLANK,
    Rac5Planets,
    Rac5SkillPoints,
    Rac5SkyboardChallenges as RACSMSKY,
)
from ..interface_orchestrator.memory.accessor import MemoryAccessor
from ..interface_orchestrator.state.base_state import BaseState
from ..interface_orchestrator.storage.local import LocalStorage
from ..interface_orchestrator.structs.address_map import AddressMap
from .address_maps import PLANET_ADDRESSES
from .structs.pickups import ClankChallengeStruct, SkyboardStruct

# Per-planet clank challenge base addresses
# Base layout (offsets from base):
#   +0  Derby unlock byte
#   +1  Gadgetbot Toss unlock byte
#   +2  Gadgetbot unlock byte
#   +3..+7   Derby challenge completions       (5 each)
#   +8..+12  Gadgetbot Toss completions        (5 each)
#   +13..+17 Gadgetbot challenge completions   (5 each)
_METALIS_BASE:    int = PLANET_ADDRESSES[0x04].clank_challenge_base  # type: ignore[assignment]
_DAYNI_BASE:      int = PLANET_ADDRESSES[0x08].clank_challenge_base  # type: ignore[assignment]
_KALIDON_SKY:     int = PLANET_ADDRESSES[0x03].skyboard_base          # type: ignore[assignment]
_OO_SKY:          int = PLANET_ADDRESSES[0x06].skyboard_base          # type: ignore[assignment]


class ChallengePickup(NamedTuple):
    address: int   # game address polled for completion; 0x00 = placeholder
    name:    str   # AP location name
    planet:  str   # AP region name


class SkyboardPickup(NamedTuple):
    unlock_addr:    int           # write 1 here at first planet load to unlock the challenge
    completed_addr: int           # poll this for completion bitmask; 0x00 = not yet confirmed
    mask:           SkyboardBit   # bit set in completed_addr when this race finishes
    name:           str           # AP location name
    planet:         str           # AP region name


class SkyboardBit(IntFlag):
    RACE_1 = 0x01
    RACE_2 = 0x04
    RACE_3 = 0x10
    RACE_4 = 0x40


# Unlock addresses (derived from base)
METALIS_CLANK_UNLOCK_ADDR:           int   = _METALIS_BASE        # +0: Derby unlock
METALIS_CLANK_UNLOCK_BYTES:          bytes = bytes([0x0F, 0x0F, 0x0F])

DAYNI_CLANK_UNLOCK_ADDR:             int   = _DAYNI_BASE          # +0: Derby unlock (alias)
DAYNI_CLANK_DERBY_UNLOCK_ADDR:       int   = _DAYNI_BASE          # +0
DAYNI_CLANK_GADGETBOT_TOSS_UNLOCK_ADDR: int = _DAYNI_BASE + 1    # +1
DAYNI_CLANK_GADGETBOT_UNLOCK_ADDR:   int   = _DAYNI_BASE + 2     # +2
DAYNI_CLANK_UNLOCK_BYTES:            bytes = bytes([0x0F, 0x0F, 0x0F])


# Clank challenge address tables (name → base + offset)
# Metalis:  Derby +3..+7 | Gadgetbot Toss +8..+12 | Gadgetbot +13..+17
# Dayni:    Derby +3..+7 | Gadgetbot Toss +8..+12 | Gadgetbot +13..+17

_METALIS_DERBY: dict[str, int] = {
    RACSMCLANK.METALIS_BUZZSAW:      _METALIS_BASE + 3,
    RACSMCLANK.METALIS_CHARGE:       _METALIS_BASE + 4,
    RACSMCLANK.METALIS_BOOGALOO:     _METALIS_BASE + 5,
    RACSMCLANK.METALIS_SHOWDOWN:     _METALIS_BASE + 6,
    RACSMCLANK.METALIS_REVENGE:      _METALIS_BASE + 7,   # reward
}

_METALIS_GADGETBOT_TOSS: dict[str, int] = {
    RACSMCLANK.METALIS_LEAGUE:       _METALIS_BASE + 8,
    RACSMCLANK.METALIS_BRACKET:      _METALIS_BASE + 9,
    RACSMCLANK.METALIS_DIVISION:     _METALIS_BASE + 10,
    RACSMCLANK.METALIS_PROFESSIONAL: _METALIS_BASE + 11,
    RACSMCLANK.METALIS_UBER:         _METALIS_BASE + 12,  # reward
}

_METALIS_GADGETBOT: dict[str, int] = {
    RACSMCLANK.METALLIS_TEAM:        _METALIS_BASE + 13,
    RACSMCLANK.METALIS_GAP:          _METALIS_BASE + 14,
    RACSMCLANK.METALIS_TELEPORTERS:  _METALIS_BASE + 15,
    RACSMCLANK.METALIS_BRAIN:        _METALIS_BASE + 16,
    RACSMCLANK.METALIS_NIGHT:        _METALIS_BASE + 17,  # reward
}

_DAYNI_DERBY: dict[str, int] = {
    RACSMCLANK.DAYNI_MOON_WELCOME:   _DAYNI_BASE + 3,
    RACSMCLANK.DAYNI_MOON_ROUND:     _DAYNI_BASE + 4,
    RACSMCLANK.DAYNI_MOON_VARIETY:   _DAYNI_BASE + 5,
    RACSMCLANK.DAYNI_MOON_SAWYER:    _DAYNI_BASE + 6,
    RACSMCLANK.DAYNI_MOON_SMASHER:   _DAYNI_BASE + 7,
}

_DAYNI_GADGETBOT_TOSS: dict[str, int] = {
    RACSMCLANK.DAYNI_MOON_HAY:        _DAYNI_BASE + 8,
    RACSMCLANK.DAYNI_MOON_TOURNAMENT: _DAYNI_BASE + 9,
    RACSMCLANK.DAYNI_MOON_AROUND:     _DAYNI_BASE + 10,
    RACSMCLANK.DAYNI_MOON_LINE:       _DAYNI_BASE + 11,
    RACSMCLANK.DAYNI_MOON_SHOWDOWN:   _DAYNI_BASE + 12,  # reward
}

_DAYNI_GADGETBOT: dict[str, int] = {
    RACSMCLANK.DAYNI_MOON_CROWD:     _DAYNI_BASE + 13,
    RACSMCLANK.DAYNI_MOON_REVERSE:   _DAYNI_BASE + 14,
    RACSMCLANK.DAYNI_MOON_BRIDGE:    _DAYNI_BASE + 15,
    RACSMCLANK.DAYNI_MOON_LEAP:      _DAYNI_BASE + 16,
    RACSMCLANK.DAYNI_MOON_INFINITE:  _DAYNI_BASE + 17,   # reward
}


# Challenge type pickup lists

DERBY_CLANK_PICKUPS: list[ChallengePickup] = [
    ChallengePickup(addr, name, Rac5Planets.METALIS)   for name, addr in _METALIS_DERBY.items()
] + [
    ChallengePickup(addr, name, Rac5Planets.DAYNI_MOON) for name, addr in _DAYNI_DERBY.items()
]

GADGETBOT_TOSS_CLANK_PICKUPS: list[ChallengePickup] = [
    ChallengePickup(addr, name, Rac5Planets.METALIS)   for name, addr in _METALIS_GADGETBOT_TOSS.items()
] + [
    ChallengePickup(addr, name, Rac5Planets.DAYNI_MOON) for name, addr in _DAYNI_GADGETBOT_TOSS.items()
]

GADGETBOT_CLANK_PICKUPS: list[ChallengePickup] = [
    ChallengePickup(addr, name, Rac5Planets.METALIS)   for name, addr in _METALIS_GADGETBOT.items()
] + [
    ChallengePickup(addr, name, Rac5Planets.DAYNI_MOON) for name, addr in _DAYNI_GADGETBOT.items()
]


# Reward locations (item grants on challenge completion)
# Subset of the above: the final challenge of each type grants an item.
CHALLENGE_PICKUPS: list[ChallengePickup] = [
    ChallengePickup(_METALIS_BASE + 3,  RACSMCLANK.METALIS_BUZZSAW,     Rac5Planets.METALIS),   # Derby first
    ChallengePickup(_METALIS_BASE + 7,  RACSMCLANK.METALIS_REVENGE,     Rac5Planets.METALIS),   # Derby reward
    ChallengePickup(_METALIS_BASE + 12, RACSMCLANK.METALIS_UBER,        Rac5Planets.METALIS),   # Gadgetbot Toss reward
    ChallengePickup(_METALIS_BASE + 17, RACSMCLANK.METALIS_NIGHT,       Rac5Planets.METALIS),   # Gadgetbot reward
    ChallengePickup(_DAYNI_BASE   + 12, RACSMCLANK.DAYNI_MOON_SHOWDOWN, Rac5Planets.DAYNI_MOON), # Gadgetbot Toss reward
    ChallengePickup(_DAYNI_BASE   + 17, RACSMCLANK.DAYNI_MOON_INFINITE, Rac5Planets.DAYNI_MOON), # Gadgetbot reward
]

CHALLENGE_ADDRESS_MAP: dict[int, str] = {
    cp.address: cp.name for cp in CHALLENGE_PICKUPS if cp.address != 0
}


# Derived maps used by ClankChallengeState

COUNT_BASED_CHALLENGE_ADDRS: frozenset[int] = frozenset(
    list(_METALIS_DERBY.values())
    + list(_METALIS_GADGETBOT_TOSS.values())
    + list(_METALIS_GADGETBOT.values())
    + list(_DAYNI_DERBY.values())
    + list(_DAYNI_GADGETBOT_TOSS.values())
    + list(_DAYNI_GADGETBOT.values())
)

ALL_CLANK_ADDRESS_MAP: dict[int, str] = {
    cp.address: cp.name
    for cp in (CHALLENGE_PICKUPS + DERBY_CLANK_PICKUPS + GADGETBOT_TOSS_CLANK_PICKUPS + GADGETBOT_CLANK_PICKUPS)
    if cp.address != 0
}

# Every individual challenge name per planet (Derby + Gadgetbot Toss + Gadgetbot).
# Used as a failsafe: if every one of these is completed, the "Ultimate Gladiator"
# skill point is sent even if its own in-game detection never fired.
METALIS_CHALLENGE_NAMES: frozenset[str] = frozenset(
    {*_METALIS_DERBY, *_METALIS_GADGETBOT_TOSS, *_METALIS_GADGETBOT}
)
DAYNI_MOON_CHALLENGE_NAMES: frozenset[str] = frozenset(
    {*_DAYNI_DERBY, *_DAYNI_GADGETBOT_TOSS, *_DAYNI_GADGETBOT}
)

GLADIATOR_FAILSAFE: dict[str, str] = {
    Rac5Planets.METALIS:    Rac5SkillPoints.METALIS_GLADIATOR,
    Rac5Planets.DAYNI_MOON: Rac5SkillPoints.DAYNI_MOON_GLADIATOR,
}


# Skyboard addresses

# Maps AP location name (constant) → (unlock_addr, completed_addr, mask).
_KALIDON_SKYBOARD: dict[str, tuple[int, int, int]] = {
    RACSMSKY.KALIDON_LEARNER: (_KALIDON_SKY, _KALIDON_SKY + 1, 0x01),
    RACSMSKY.KALIDON_TICKET:  (_KALIDON_SKY, _KALIDON_SKY + 1, 0x04),
    RACSMSKY.KALIDON_TRICKY:  (_KALIDON_SKY, _KALIDON_SKY + 1, 0x10),
    RACSMSKY.KALIDON_MASTER:  (_KALIDON_SKY, _KALIDON_SKY + 1, 0x40),
}

_OUTPOST_OMEGA_SKYBOARD: dict[str, tuple[int, int, int]] = {
    RACSMSKY.OUTPOST_OMEGA_INTERIOR: (_OO_SKY, _OO_SKY + 1, 0x01),
    RACSMSKY.OUTPOST_OMEGA_DANGER:   (_OO_SKY, _OO_SKY + 1, 0x04),
    RACSMSKY.OUTPOST_OMEGA_VORTEX:   (_OO_SKY, _OO_SKY + 1, 0x10),
    RACSMSKY.OUTPOST_OMEGA_VERTIGO:  (_OO_SKY, _OO_SKY + 1, 0x40),
}

KALIDON_SKYBOARD_PICKUPS: list[SkyboardPickup] = [
    SkyboardPickup(unlock_addr, completed_addr, SkyboardBit(mask), name, Rac5Planets.KALIDON)
    for name, (unlock_addr, completed_addr, mask) in _KALIDON_SKYBOARD.items()
]

OUTPOST_OMEGA_SKYBOARD_PICKUPS: list[SkyboardPickup] = [
    SkyboardPickup(unlock_addr, completed_addr, SkyboardBit(mask), name, Rac5Planets.OUTPOST_OMEGA)
    for name, (unlock_addr, completed_addr, mask) in _OUTPOST_OMEGA_SKYBOARD.items()
]

ALL_SKYBOARD_PICKUPS: list[SkyboardPickup] = KALIDON_SKYBOARD_PICKUPS + OUTPOST_OMEGA_SKYBOARD_PICKUPS

SKYBOARD_ADDRESS_MASK_MAP: dict[tuple[int, int], str] = {
    (sp.completed_addr, int(sp.mask)): sp.name
    for sp in ALL_SKYBOARD_PICKUPS
    if sp.completed_addr != 0
}

SKYBOARD_UNLOCK_MASK: dict[int, int] = {}
for _sp in ALL_SKYBOARD_PICKUPS:
    if _sp.unlock_addr != 0:
        SKYBOARD_UNLOCK_MASK[_sp.unlock_addr] = SKYBOARD_UNLOCK_MASK.get(_sp.unlock_addr, 0) | int(_sp.mask)


# Challenge-only AP items
CHALLENGE_ONLY_ITEMS: frozenset[str] = frozenset({
    "Polarizer",
    "Sludge Mk9 Gloves",
    "Crystallix Helmet",
    "Crystallix Gloves",
    "Mega Bomb Gloves",
    "Mega Bomb Boots",
    "Electroshock Boots",
})


# Clank challenge state (runtime)

class ClankChallengeState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self._completed: set[str]                     = set()
        self._metalis_counts: dict[int, int]          = {}
        self._on_location_check: Callable[[str], None] = lambda _: None
        self._all_challenges: bool                    = False
        self._enabled:        bool                    = True
        self._gladiator_sent: set[str]                = set()

    def set_mode(self, mode: int) -> None:
        self._enabled       = mode >= 1
        self._all_challenges = mode >= 2

    def set_location_check_callback(self, cb: Callable[[str], None]) -> None:
        self._on_location_check = cb

    def on_exit(self) -> None:
        self._on_location_check = lambda _: None

    def _register_handlers(self) -> None:
        if self._enabled:
            self.accessor.on_struct_change(ClankChallengeStruct, self._on_region_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(ClankChallengeStruct, self._on_region_change)

    def _on_region_change(self, address: int, new_bytes: bytes) -> None:
        del address, new_bytes
        addr_map = ALL_CLANK_ADDRESS_MAP if self._all_challenges else CHALLENGE_ADDRESS_MAP
        for addr, name in addr_map.items():
            if name in self._completed:
                continue
            raw = self.accessor.read_raw(addr, 1)
            count = raw[0] if raw else 0
            if addr in COUNT_BASED_CHALLENGE_ADDRS:
                prev = self._metalis_counts.get(addr, 0)
                self._metalis_counts[addr] = count
                if count > prev:
                    self._completed.add(name)
                    self._on_location_check(name)
                    self.on_challenge_completed(name)
                    self._check_gladiator_failsafe()
            else:
                if count >= 2:
                    self._completed.add(name)
                    self._on_location_check(name)
                    self.on_challenge_completed(name)
                    self._check_gladiator_failsafe()

    def _check_gladiator_failsafe(self) -> None:
        """If every individual challenge on a planet is complete, send that
        planet's Ultimate Gladiator skill point even if its own in-game
        detection never fired."""
        if Rac5Planets.METALIS not in self._gladiator_sent and METALIS_CHALLENGE_NAMES <= self._completed:
            self._gladiator_sent.add(Rac5Planets.METALIS)
            self._on_location_check(GLADIATOR_FAILSAFE[Rac5Planets.METALIS])
        if Rac5Planets.DAYNI_MOON not in self._gladiator_sent and DAYNI_MOON_CHALLENGE_NAMES <= self._completed:
            self._gladiator_sent.add(Rac5Planets.DAYNI_MOON)
            self._on_location_check(GLADIATOR_FAILSAFE[Rac5Planets.DAYNI_MOON])

    def sync(self) -> None:
        for addr, name in ALL_CLANK_ADDRESS_MAP.items():
            raw = self.accessor.read_raw(addr, 1)
            count = raw[0] if raw else 0
            if addr in COUNT_BASED_CHALLENGE_ADDRS:
                self._metalis_counts[addr] = count
                if count > 0:
                    self._completed.add(name)
            else:
                if count >= 2:
                    self._completed.add(name)

    def write_unlocks(self) -> None:
        if not self._enabled:
            return
        self.accessor.write_raw(METALIS_CLANK_UNLOCK_ADDR, METALIS_CLANK_UNLOCK_BYTES)
        self.accessor.write_raw(DAYNI_CLANK_UNLOCK_ADDR, DAYNI_CLANK_UNLOCK_BYTES)

    def write_defaults(self) -> None:
        if not self._enabled:
            return
        self.write_unlocks()
        if self._all_challenges:
            return  # don't preset values — every completion is a check
        for addr in ALL_CLANK_ADDRESS_MAP:
            if addr not in COUNT_BASED_CHALLENGE_ADDRS:
                raw = self.accessor.read_raw(addr, 1)
                if raw and raw[0] == 0:
                    self.accessor.write_raw(addr, b"\x01")

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        self._completed.update(
            name for name in checked_locations if name in ALL_CLANK_ADDRESS_MAP.values()
        )

    def on_challenge_completed(self, _name: str) -> None:
        del _name

    def __repr__(self) -> str:
        return f"ClankChallengeState(completed={len(self._completed)}/{len(ALL_CLANK_ADDRESS_MAP)})"

class SkyboardChallengeState(BaseState):
    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self._completed: set[str]                     = set()
        self._on_location_check: Callable[[str], None] = lambda _: None
        self._enabled: bool                           = True

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def set_location_check_callback(self, cb: Callable[[str], None]) -> None:
        self._on_location_check = cb

    def on_exit(self) -> None:
        self._on_location_check = lambda _: None

    def _register_handlers(self) -> None:
        if self._enabled:
            self.accessor.on_struct_change(SkyboardStruct, self._on_region_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(SkyboardStruct, self._on_region_change)

    def _on_region_change(self, address: int, new_bytes: bytes) -> None:
        del address, new_bytes
        for (addr, mask), name in SKYBOARD_ADDRESS_MASK_MAP.items():
            if name not in self._completed:
                val = self.accessor.read_raw(addr, 1)
                if val and (val[0] & mask):
                    self._completed.add(name)
                    self._on_location_check(name)
                    self.on_race_completed(name)

    def sync(self) -> None:
        for (addr, mask), name in SKYBOARD_ADDRESS_MASK_MAP.items():
            val = self.accessor.read_raw(addr, 1)
            if val and (val[0] & mask):
                self._completed.add(name)

    def write_defaults(self) -> None:
        pass

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        self._completed.update(
            name for name in checked_locations if name in SKYBOARD_ADDRESS_MASK_MAP.values()
        )

    def on_race_completed(self, _name: str) -> None:
        del _name

    def __repr__(self) -> str:
        return f"SkyboardChallengeState(completed={len(self._completed)}/{len(SKYBOARD_ADDRESS_MASK_MAP)})"

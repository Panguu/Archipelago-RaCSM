from __future__ import annotations

from enum import IntEnum, IntFlag
from typing import NamedTuple

from ...constants import (
    Rac5ClankChallenges,
    Rac5Planets,
    Rac5SkillPoints,
    Rac5SkyboardChallenges,
)
from ..address_maps import PLANET_ADDRESSES

# Per-planet clank challenge base addresses: +0/+1/+2 are section unlock bytes,
# +3..+17 are 5-per-section completion bytes (Derby, Gadgetbot Toss, Gadgetbot).
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


class ChallengeSection(IntEnum):
    """The three independently-unlockable clank challenge sections on a planet."""

    DERBY           = 0
    GADGETBOT_TOSS  = 1
    GADGETBOT       = 2


METALIS_CLANK_UNLOCK_ADDR:           int   = _METALIS_BASE        # +0: Derby unlock
METALIS_CLANK_UNLOCK_BYTES:          bytes = bytes([0x0F, 0x0F, 0x0F])

DAYNI_CLANK_UNLOCK_ADDR:             int   = _DAYNI_BASE          # +0: Derby unlock (alias)
DAYNI_CLANK_DERBY_UNLOCK_ADDR:       int   = _DAYNI_BASE          # +0
DAYNI_CLANK_GADGETBOT_TOSS_UNLOCK_ADDR: int = _DAYNI_BASE + 1    # +1
DAYNI_CLANK_GADGETBOT_UNLOCK_ADDR:   int   = _DAYNI_BASE + 2     # +2
DAYNI_CLANK_UNLOCK_BYTES:            bytes = bytes([0x0F, 0x0F, 0x0F])

# Per-planet, per-section unlock byte address — lets a caller unlock just one
# of the three sections (e.g. Derby only) instead of all three at once.
CLANK_SECTION_UNLOCK_ADDRESSES: dict[str, dict[ChallengeSection, int]] = {
    Rac5Planets.METALIS: {
        ChallengeSection.DERBY:          _METALIS_BASE,
        ChallengeSection.GADGETBOT_TOSS: _METALIS_BASE + 1,
        ChallengeSection.GADGETBOT:      _METALIS_BASE + 2,
    },
    Rac5Planets.DAYNI_MOON: {
        ChallengeSection.DERBY:          _DAYNI_BASE,
        ChallengeSection.GADGETBOT_TOSS: _DAYNI_BASE + 1,
        ChallengeSection.GADGETBOT:      _DAYNI_BASE + 2,
    },
}


_METALIS_DERBY: dict[str, int] = {
    Rac5ClankChallenges.METALIS_BUZZSAW:      _METALIS_BASE + 3,
    Rac5ClankChallenges.METALIS_CHARGE:       _METALIS_BASE + 4,
    Rac5ClankChallenges.METALIS_BOOGALOO:     _METALIS_BASE + 5,
    Rac5ClankChallenges.METALIS_SHOWDOWN:     _METALIS_BASE + 6,
    Rac5ClankChallenges.METALIS_REVENGE:      _METALIS_BASE + 7,   # reward
}

_METALIS_GADGETBOT_TOSS: dict[str, int] = {
    Rac5ClankChallenges.METALIS_LEAGUE:       _METALIS_BASE + 8,
    Rac5ClankChallenges.METALIS_BRACKET:      _METALIS_BASE + 9,
    Rac5ClankChallenges.METALIS_DIVISION:     _METALIS_BASE + 10,
    Rac5ClankChallenges.METALIS_PROFESSIONAL: _METALIS_BASE + 11,
    Rac5ClankChallenges.METALIS_UBER:         _METALIS_BASE + 12,  # reward
}

_METALIS_GADGETBOT: dict[str, int] = {
    Rac5ClankChallenges.METALLIS_TEAM:        _METALIS_BASE + 13,
    Rac5ClankChallenges.METALIS_GAP:          _METALIS_BASE + 14,
    Rac5ClankChallenges.METALIS_TELEPORTERS:  _METALIS_BASE + 15,
    Rac5ClankChallenges.METALIS_BRAIN:        _METALIS_BASE + 16,
    Rac5ClankChallenges.METALIS_NIGHT:        _METALIS_BASE + 17,  # reward
}

_DAYNI_DERBY: dict[str, int] = {
    Rac5ClankChallenges.DAYNI_MOON_WELCOME:   _DAYNI_BASE + 3,
    Rac5ClankChallenges.DAYNI_MOON_ROUND:     _DAYNI_BASE + 4,
    Rac5ClankChallenges.DAYNI_MOON_VARIETY:   _DAYNI_BASE + 5,
    Rac5ClankChallenges.DAYNI_MOON_SAWYER:    _DAYNI_BASE + 6,
    Rac5ClankChallenges.DAYNI_MOON_SMASHER:   _DAYNI_BASE + 7,
}

_DAYNI_GADGETBOT_TOSS: dict[str, int] = {
    Rac5ClankChallenges.DAYNI_MOON_HAY:        _DAYNI_BASE + 8,
    Rac5ClankChallenges.DAYNI_MOON_TOURNAMENT: _DAYNI_BASE + 9,
    Rac5ClankChallenges.DAYNI_MOON_AROUND:     _DAYNI_BASE + 10,
    Rac5ClankChallenges.DAYNI_MOON_LINE:       _DAYNI_BASE + 11,
    Rac5ClankChallenges.DAYNI_MOON_SHOWDOWN:   _DAYNI_BASE + 12,  # reward
}

_DAYNI_GADGETBOT: dict[str, int] = {
    Rac5ClankChallenges.DAYNI_MOON_CROWD:     _DAYNI_BASE + 13,
    Rac5ClankChallenges.DAYNI_MOON_REVERSE:   _DAYNI_BASE + 14,
    Rac5ClankChallenges.DAYNI_MOON_BRIDGE:    _DAYNI_BASE + 15,
    Rac5ClankChallenges.DAYNI_MOON_LEAP:      _DAYNI_BASE + 16,
    Rac5ClankChallenges.DAYNI_MOON_INFINITE:  _DAYNI_BASE + 17,   # reward
}


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
    ChallengePickup(_METALIS_BASE + 3,  Rac5ClankChallenges.METALIS_BUZZSAW,     Rac5Planets.METALIS),    # Derby first
    ChallengePickup(_METALIS_BASE + 7,  Rac5ClankChallenges.METALIS_REVENGE,     Rac5Planets.METALIS),    # Derby reward
    # Gadgetbot Toss reward
    ChallengePickup(_METALIS_BASE + 12, Rac5ClankChallenges.METALIS_UBER,        Rac5Planets.METALIS),
    # Gadgetbot reward
    ChallengePickup(_METALIS_BASE + 17, Rac5ClankChallenges.METALIS_NIGHT,       Rac5Planets.METALIS),
    # Gadgetbot Toss reward
    ChallengePickup(_DAYNI_BASE   + 12, Rac5ClankChallenges.DAYNI_MOON_SHOWDOWN, Rac5Planets.DAYNI_MOON),
    # Gadgetbot reward
    ChallengePickup(_DAYNI_BASE   + 17, Rac5ClankChallenges.DAYNI_MOON_INFINITE, Rac5Planets.DAYNI_MOON),
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

# Every challenge name per planet; used as a failsafe to award the "Ultimate
# Gladiator" skill point if all are done but its own in-game detection never fired.
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

# ClankChallengeGroups option: group name per location, used to filter location
# creation (regions.py) and rule assignment (rules/*.py) by group weight.
CHALLENGE_GROUP_DERBY:          str = "Demolition Derby"
CHALLENGE_GROUP_GADGETBOT_TOSS: str = "Gadgetbot Toss"
CHALLENGE_GROUP_GADGETBOT:      str = "Gadgetbot"

CHALLENGE_NAME_TO_GROUP: dict[str, str] = {
    **dict.fromkeys((*_METALIS_DERBY, *_DAYNI_DERBY), CHALLENGE_GROUP_DERBY),
    **dict.fromkeys((*_METALIS_GADGETBOT_TOSS, *_DAYNI_GADGETBOT_TOSS), CHALLENGE_GROUP_GADGETBOT_TOSS),
    **dict.fromkeys((*_METALIS_GADGETBOT, *_DAYNI_GADGETBOT), CHALLENGE_GROUP_GADGETBOT),
}


# Maps AP location name (constant) → (unlock_addr, completed_addr, mask).
_KALIDON_SKYBOARD: dict[str, tuple[int, int, int]] = {
    Rac5SkyboardChallenges.KALIDON_LEARNER: (_KALIDON_SKY, _KALIDON_SKY + 1, 0x01),
    Rac5SkyboardChallenges.KALIDON_TICKET:  (_KALIDON_SKY, _KALIDON_SKY + 1, 0x04),
    Rac5SkyboardChallenges.KALIDON_TRICKY:  (_KALIDON_SKY, _KALIDON_SKY + 1, 0x10),
    Rac5SkyboardChallenges.KALIDON_MASTER:  (_KALIDON_SKY, _KALIDON_SKY + 1, 0x40),
}

_OUTPOST_OMEGA_SKYBOARD: dict[str, tuple[int, int, int]] = {
    Rac5SkyboardChallenges.OUTPOST_OMEGA_INTERIOR: (_OO_SKY, _OO_SKY + 1, 0x01),
    Rac5SkyboardChallenges.OUTPOST_OMEGA_DANGER:   (_OO_SKY, _OO_SKY + 1, 0x04),
    Rac5SkyboardChallenges.OUTPOST_OMEGA_VORTEX:   (_OO_SKY, _OO_SKY + 1, 0x10),
    Rac5SkyboardChallenges.OUTPOST_OMEGA_VERTIGO:  (_OO_SKY, _OO_SKY + 1, 0x40),
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


CHALLENGE_ONLY_ITEMS: frozenset[str] = frozenset({
    "Polarizer",
    "Sludge Mk9 Gloves",
    "Crystallix Helmet",
    "Crystallix Gloves",
    "Mega Bomb Gloves",
    "Mega Bomb Boots",
    "Electroshock Boots",
})

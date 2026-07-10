from __future__ import annotations

from ...constants import Rac5CutsceneLocations
from ..address_maps import PLANET_MISSION_ADDRESSES

# Maps (address, mask) -> location_name.
# Detection: (current_value & mask) != 0
# mask of 0x0000 means not yet validated — skipped by MissionInventory.

_ADDRS = PLANET_MISSION_ADDRESSES

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

# Combined (used by MissionInventory to watch all possible completions)
MISSION_COMPLETE_MAP: dict[tuple[int, int], str] = {**STORY_MISSION_MAP, **CUTSCENE_MAP}

VALIDATED_MISSION_MAP: dict[tuple[int, int], str] = {
    k: v for k, v in MISSION_COMPLETE_MAP.items() if k[1] != 0x0000
}

# Reverse map: address -> planet name for log messages
PLANET_BY_ADDR: dict[int, str] = {v: k for k, v in PLANET_MISSION_ADDRESSES.items()}

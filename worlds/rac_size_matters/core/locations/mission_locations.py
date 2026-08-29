from __future__ import annotations

from ...constants import Rac5CutsceneLocations
from ..address_maps import PLANET_ADDRESSES, PLANET_MISSION_ADDRESSES

# Maps (address, mask) -> location_name; detected via (value & mask) != 0.
# mask of 0x0000 means not yet validated — skipped by MissionInventory.

_ADDRS = PLANET_MISSION_ADDRESSES

STORY_MISSION_MAP: dict[tuple[int, int], str] = {
    # Story-required prerequisite bits, previously force-written every load so they
    # never surfaced; now tracked for real, each completion force-reloads its planet.
    (_ADDRS["Pokitaru"],      0x0004): Rac5CutsceneLocations.POKITARU_RESCUE,
    (_ADDRS["Kalidon"],       0x0004): Rac5CutsceneLocations.KALIDON_SEARCH,
    (_ADDRS["Challax"],       0x0004): Rac5CutsceneLocations.CHALLAX_EXPLORE,

    (_ADDRS["Pokitaru"],      0x0002): Rac5CutsceneLocations.POKITARU_FIGHT,

    (_ADDRS["Ryllus"],        0x0008): Rac5CutsceneLocations.RYLLUS_ARTIFACT,
    (_ADDRS["Ryllus"],        0x0010): Rac5CutsceneLocations.RYLLUS_TEMPLE,

    (_ADDRS["Kalidon"],       0x0010): Rac5CutsceneLocations.KALIDON_WIN,

    (_ADDRS["Metalis"],       0x0002): Rac5CutsceneLocations.METALIS_WAR,
    # METALIS_ESCAPE is NOT mapped here — it's fired directly by
    # PlanetInventory.check_giant_clank() to avoid double-detection via MissionInventory.

    (_ADDRS["Dreamtime"],     0x0004): Rac5CutsceneLocations.DREAMTIME_COMPLETE,

    (_ADDRS["Outpost Omega"], 0x0080): Rac5CutsceneLocations.OUTPOST_OMEGA_ESCAPE,
    (_ADDRS["Outpost Omega"], 0x0010): Rac5CutsceneLocations.OUTPOST_OMEGA_REMATCH,

    # CHALLAX_CLANK is NOT mapped here — same reasoning as METALIS_ESCAPE
    # above: fired directly by PlanetInventory.check_giant_clank().

    (_ADDRS["Dayni Moon"],    0x0008): Rac5CutsceneLocations.DAYNI_MOON,
    (_ADDRS["Dayni Moon"],    0x0004): Rac5CutsceneLocations.DAYNI_MOON_LUNA,
    (_ADDRS["Dayni Moon"],    0x0020): Rac5CutsceneLocations.INSIDE_CLANK_ESCAPE,

    (_ADDRS["Inside Clank"],  0x0002): Rac5CutsceneLocations.INSIDE_CLANK_TECHNOMITES,

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
    # METALIS_CLANK is the shared Giant-Clank-trigger bit both sequences set on start; not tracked as a location, unlike CHALLAX_CLANK/METALIS_ESCAPE.
    # (_ADDRS["Challax"],     0x0010): Rac5CutsceneLocations.METALIS_CLANK,
    (_ADDRS["Dayni Moon"],    0x0010): Rac5CutsceneLocations.DAYNI_MOON_FIGHT1,
    (_ADDRS["Dayni Moon"],    0x0002): Rac5CutsceneLocations.DAYNI_MOON_FIGHT2,
    (_ADDRS["Dreamtime"],     0x0002): Rac5CutsceneLocations.DREAMTIME_SLEEPING_RATCHET,
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

# planet name (PLANET_MISSION_ADDRESSES key, matches PlanetAddresses.name) -> planet id
_PLANET_ID_BY_NAME: dict[str, int] = {p.name: pid for pid, p in PLANET_ADDRESSES.items()}

# Location name -> planet id; MissionInventory.check() uses this to refuse a completion
# unless the player is on that planet, since these bits are readable cross-planet too.
LOCATION_TO_PLANET_ID: dict[str, int] = {
    name: _PLANET_ID_BY_NAME[PLANET_BY_ADDR[address]]
    for (address, _mask), name in VALIDATED_MISSION_MAP.items()
    if PLANET_BY_ADDR[address] in _PLANET_ID_BY_NAME
}

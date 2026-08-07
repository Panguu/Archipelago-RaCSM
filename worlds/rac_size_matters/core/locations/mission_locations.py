from __future__ import annotations

from ...constants import Rac5CutsceneLocations
from ..address_maps import PLANET_MISSION_ADDRESSES

# Maps (address, mask) -> location_name.
# Detection: (current_value & mask) != 0
# mask of 0x0000 means not yet validated — skipped by MissionInventory.

_ADDRS = PLANET_MISSION_ADDRESSES

STORY_MISSION_MAP: dict[tuple[int, int], str] = {
    # Story-required prerequisite bits — previously force-written on every
    # load (PRESET_MISSION_BITS) so the game skipped them entirely and they
    # never surfaced as checks. Now tracked for real: completing each one
    # force-reloads its own planet (see core/core.py's _MISSION_FORCE_RELOAD),
    # replacing whatever the force-write used to paper over.
    (_ADDRS["Pokitaru"],      0x0004): Rac5CutsceneLocations.POKITARU_RESCUE,
    (_ADDRS["Kalidon"],       0x0004): Rac5CutsceneLocations.KALIDON_SEARCH,
    (_ADDRS["Challax"],       0x0004): Rac5CutsceneLocations.CHALLAX_EXPLORE,

    (_ADDRS["Pokitaru"],      0x0002): Rac5CutsceneLocations.POKITARU_FIGHT,

    (_ADDRS["Ryllus"],        0x0008): Rac5CutsceneLocations.RYLLUS_ARTIFACT,
    (_ADDRS["Ryllus"],        0x0010): Rac5CutsceneLocations.RYLLUS_TEMPLE,

    (_ADDRS["Kalidon"],       0x0010): Rac5CutsceneLocations.KALIDON_WIN,

    (_ADDRS["Metalis"],       0x0002): Rac5CutsceneLocations.METALIS_WAR,
    # METALIS_ESCAPE is NOT mapped here — it's fired directly by
    # PlanetInventory.check_giant_clank() (see core/planets.py), which
    # watches the game's own scripted exit transition rather than this bit,
    # so it isn't double-detected through MissionInventory too.

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
    # METALIS_CLANK is the shared Giant-Clank-trigger bit both sequences set
    # on start (see planets.py's GIANT_CLANK_CONFIGS note) — still not
    # tracked as a location, unlike CHALLAX_CLANK/METALIS_ESCAPE above.
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

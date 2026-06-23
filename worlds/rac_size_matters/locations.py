from typing import NamedTuple

from .constants import (
    RACSMLOCATION,
    RACSMPLANET,
    RACSMSKYBOARDCHALLENGE as RACSMSKY,
    RACSMVENDORLOCATION,
    RacSMCutsceneLocations,
)
from .core.armour import ARMOUR_PICKUPS
from .core.challenges import (
    CHALLENGE_PICKUPS,
    DERBY_CLANK_PICKUPS,
    GADGETBOT_CLANK_PICKUPS,
    GADGETBOT_TOSS_CLANK_PICKUPS,
)
from .core.skill_points import (
    CLANK_CHALLENGE_SKILL_POINTS,
    HARD_SKILL_POINTS,
    SKILL_POINTS,
    SKYBOARD_CHALLENGE_SKILL_POINTS,
)
from .core.titanium_bolts import TITANIUM_BOLTS

BASE_ID = 77_700_000


class RACLocationData(NamedTuple):
    code: int
    region: str


TITANIUM_BOLT_LOCATIONS: dict[str, RACLocationData] = {
    name: RACLocationData(BASE_ID + 1000 + idx, bolt.region)
    for idx, (name, bolt) in enumerate(TITANIUM_BOLTS.items(), start=1)
}

ARMOUR_PICKUP_LOCATIONS: dict[str, RACLocationData] = {
    ap.name: RACLocationData(BASE_ID + 1100 + idx, ap.planet)
    for idx, ap in enumerate(ARMOUR_PICKUPS, start=1)
}


BOSS_LOCATIONS: dict[str, RACLocationData] = {
    RACSMLOCATION.QUODRONA_GOAL: RACLocationData(BASE_ID + 1200, RACSMPLANET.QUODRONA),
}

# ── Weapon vendor locations ───────────────────────────────────────────────────
WEAPON_VENDOR_LOCATIONS: dict[str, RACLocationData] = {
    RACSMVENDORLOCATION.POKITARU_LACERATOR:  RACLocationData(BASE_ID + 2001, RACSMPLANET.POKITARU),
    RACSMVENDORLOCATION.POKITARU_ACID:       RACLocationData(BASE_ID + 2002, RACSMPLANET.POKITARU),
    RACSMVENDORLOCATION.POKITARU_CONCUSSION: RACLocationData(BASE_ID + 2003, RACSMPLANET.POKITARU),
    RACSMVENDORLOCATION.RYLLUS_AGENTS:       RACLocationData(BASE_ID + 2004, RACSMPLANET.RYLLUS),
    RACSMVENDORLOCATION.KALIDON_SCORCHER:    RACLocationData(BASE_ID + 2005, RACSMPLANET.KALIDON),
    RACSMVENDORLOCATION.DREAMTIME_SUCK:      RACLocationData(BASE_ID + 2006, RACSMPLANET.DREAMTIME),
    RACSMVENDORLOCATION.OUTPOST_OMEGA_BEE:   RACLocationData(BASE_ID + 2007, RACSMPLANET.OUTPOST_OMEGA),
    RACSMVENDORLOCATION.CHALLAX_SNIPER:      RACLocationData(BASE_ID + 2008, RACSMPLANET.CHALLAX),
    RACSMVENDORLOCATION.DAYNI_MOON_SHOCK:    RACLocationData(BASE_ID + 2009, RACSMPLANET.DAYNI_MOON),
    RACSMVENDORLOCATION.INSIDE_CLANK_STATIC: RACLocationData(BASE_ID + 2010, RACSMPLANET.INSIDE_CLANK),
    RACSMVENDORLOCATION.QUODRONA_LASER:      RACLocationData(BASE_ID + 2011, RACSMPLANET.QUODRONA),
}

# ── Gadget vendor locations ───────────────────────────────────────────────────
GADGET_VENDOR_LOCATIONS: dict[str, RACLocationData] = {
    RACSMVENDORLOCATION.POKITARU_HYPERSHOT:      RACLocationData(BASE_ID + 2101, RACSMPLANET.POKITARU),
    RACSMVENDORLOCATION.CHALLAX_PDA:             RACLocationData(BASE_ID + 2102, RACSMPLANET.CHALLAX),
    RACSMVENDORLOCATION.DAYNI_MOON_MAP:          RACLocationData(BASE_ID + 2103, RACSMPLANET.DAYNI_MOON),
    RACSMVENDORLOCATION.CHALLAX_BOLT_GRABBER:    RACLocationData(BASE_ID + 2104, RACSMPLANET.CHALLAX),
    RACSMVENDORLOCATION.OUTPOST_OMEGA_BOX_BREAKER: RACLocationData(BASE_ID + 2105, RACSMPLANET.OUTPOST_OMEGA),
}

# ── Weapon mod vendor locations ───────────────────────────────────────────────
WEAPON_MOD_VENDOR_LOCATIONS: dict[str, RACLocationData] = {
    RACSMVENDORLOCATION.KALIDON_LACERATOR_LOCK:    RACLocationData(BASE_ID + 2202, RACSMPLANET.KALIDON),
    RACSMVENDORLOCATION.KALIDON_CONCUSSION_SPLIT:  RACLocationData(BASE_ID + 2205, RACSMPLANET.KALIDON),
    RACSMVENDORLOCATION.CHALLAX_LACERATOR_DOUBLE:  RACLocationData(BASE_ID + 2201, RACSMPLANET.CHALLAX),
    RACSMVENDORLOCATION.CHALLAX_ACID_BURN:         RACLocationData(BASE_ID + 2203, RACSMPLANET.CHALLAX),
    RACSMVENDORLOCATION.CHALLAX_ACID_EPOXY:        RACLocationData(BASE_ID + 2204, RACSMPLANET.CHALLAX),
    RACSMVENDORLOCATION.CHALLAX_CONCUSSION_LOCK:   RACLocationData(BASE_ID + 2206, RACSMPLANET.CHALLAX),
    RACSMVENDORLOCATION.CHALLAX_CONCUSSION_CHARGE: RACLocationData(BASE_ID + 2207, RACSMPLANET.CHALLAX),
    RACSMVENDORLOCATION.CHALLAX_BEE_WORKER:        RACLocationData(BASE_ID + 2211, RACSMPLANET.CHALLAX),
    RACSMVENDORLOCATION.QUODRONA_AGENTS_LAUNCHER:  RACLocationData(BASE_ID + 2209, RACSMPLANET.QUODRONA),
    RACSMVENDORLOCATION.QUODRONA_SCORCHER_SPITFIRE: RACLocationData(BASE_ID + 2210, RACSMPLANET.QUODRONA),
    RACSMVENDORLOCATION.QUODRONA_SNIPER_SPLIT:     RACLocationData(BASE_ID + 2212, RACSMPLANET.QUODRONA),
    RACSMVENDORLOCATION.QUODRONA_SHOCK_LOCK:       RACLocationData(BASE_ID + 2213, RACSMPLANET.QUODRONA),
    RACSMVENDORLOCATION.QUODRONA_SHOCK_AFTER:      RACLocationData(BASE_ID + 2214, RACSMPLANET.QUODRONA),
}

from .core.armour import ARMOUR_SET_CHECKS

ARMOUR_SET_CHECK_LOCATIONS: dict[str, RACLocationData] = {
    name: RACLocationData(BASE_ID + 1500 + idx, RACSMPLANET.POKITARU)
    for idx, name in enumerate(ARMOUR_SET_CHECKS, start=1)
}

SKILL_POINT_LOCATIONS: dict[str, RACLocationData] = {
    name: RACLocationData(BASE_ID + 4000 + idx, sp.region)
    for idx, (name, sp) in enumerate(SKILL_POINTS.items(), start=1)
}

EASY_SKILL_POINT_LOCATIONS: dict[str, RACLocationData] = {
    name: data for name, data in SKILL_POINT_LOCATIONS.items()
    if name not in HARD_SKILL_POINTS
    and name not in CLANK_CHALLENGE_SKILL_POINTS
    and name not in SKYBOARD_CHALLENGE_SKILL_POINTS
}

HARD_SKILL_POINT_LOCATIONS: dict[str, RACLocationData] = {
    name: data for name, data in SKILL_POINT_LOCATIONS.items()
    if name in HARD_SKILL_POINTS
}

CLANK_CHALLENGE_SKILL_POINT_LOCATIONS: dict[str, RACLocationData] = {
    name: data for name, data in SKILL_POINT_LOCATIONS.items()
    if name in CLANK_CHALLENGE_SKILL_POINTS
}

SKYBOARD_CHALLENGE_SKILL_POINT_LOCATIONS: dict[str, RACLocationData] = {
    name: data for name, data in SKILL_POINT_LOCATIONS.items()
    if name in SKYBOARD_CHALLENGE_SKILL_POINTS
}

GADGET_PICKUP_LOCATIONS: dict[str, RACLocationData] = {
    RACSMLOCATION.RYLLUS_SPROUT:  RACLocationData(BASE_ID + 1401, RACSMPLANET.RYLLUS),
    RACSMLOCATION.KALIDON_SHRINK: RACLocationData(BASE_ID + 1407, RACSMPLANET.KALIDON),
    # RACSMLOCATION.METALIS_GLOVES: RACLocationData(BASE_ID + 1406, RACSMPLANET.METALIS),  # Giant Clank disabled
}

# ── Skyboard challenge locations ──────────────────────────────────────────────
SKYBOARD_ITEM_LOCATIONS: dict[str, RACLocationData] = {
    RACSMSKY.KALIDON_LEARNER:          RACLocationData(BASE_ID + 1402, RACSMPLANET.KALIDON),
    RACSMSKY.KALIDON_MASTER:           RACLocationData(BASE_ID + 1405, RACSMPLANET.KALIDON),
    RACSMSKY.OUTPOST_OMEGA_VERTIGO:    RACLocationData(BASE_ID + 1800, RACSMPLANET.OUTPOST_OMEGA),
    RACSMSKY.OUTPOST_OMEGA_INTERIOR:   RACLocationData(BASE_ID + 1801, RACSMPLANET.OUTPOST_OMEGA),
}

EXTRA_SKYBOARD_LOCATIONS: dict[str, RACLocationData] = {
    RACSMSKY.KALIDON_TICKET:           RACLocationData(BASE_ID + 1403, RACSMPLANET.KALIDON),
    RACSMSKY.KALIDON_TRICKY:           RACLocationData(BASE_ID + 1404, RACSMPLANET.KALIDON),
    RACSMSKY.OUTPOST_OMEGA_DANGER:     RACLocationData(BASE_ID + 1802, RACSMPLANET.OUTPOST_OMEGA),
    RACSMSKY.OUTPOST_OMEGA_VORTEX:     RACLocationData(BASE_ID + 1803, RACSMPLANET.OUTPOST_OMEGA),
}

CHALLENGE_LOCATIONS: dict[str, RACLocationData] = {
    cp.name: RACLocationData(BASE_ID + 1600 + idx, cp.planet)
    for idx, cp in enumerate(CHALLENGE_PICKUPS, start=1)
}

_ALL_CLANK_PICKUPS = DERBY_CLANK_PICKUPS + GADGETBOT_TOSS_CLANK_PICKUPS + GADGETBOT_CLANK_PICKUPS
ALL_CLANK_LOCATIONS: dict[str, RACLocationData] = {
    cp.name: RACLocationData(BASE_ID + 1700 + idx, cp.planet)
    for idx, cp in enumerate(_ALL_CLANK_PICKUPS, start=1)
    if cp.name not in CHALLENGE_LOCATIONS  # combined reward-challenge names live in CHALLENGE_LOCATIONS
}

# Each entry: (name, region, is_cutscene).
# Enumeration order is fixed to keep location IDs stable across option changes.
# Enter Planet entries are appended at the end to avoid shifting existing IDs.
_MISSION_ENTRIES: list[tuple[str, str, bool]] = [
    # Pokitaru
    (RacSMCutsceneLocations.POKITARU_FIGHT,           RACSMPLANET.POKITARU,      False),
    # Ryllus
    (RacSMCutsceneLocations.RYLLUS_BUZZING,           RACSMPLANET.RYLLUS,        True),
    (RacSMCutsceneLocations.RYLLUS_ARTIFACT,          RACSMPLANET.RYLLUS,        False),
    (RacSMCutsceneLocations.RYLLUS_TEMPLE,            RACSMPLANET.RYLLUS,        False),
    # Kalidon
    (RacSMCutsceneLocations.KALIDON_EXPLORE,          RACSMPLANET.KALIDON,       True),
    (RacSMCutsceneLocations.KALIDON_WIN,              RACSMPLANET.KALIDON,       False),
    # Metalis
    (RacSMCutsceneLocations.METALIS_WAR,              RACSMPLANET.METALIS,       False),
    # (RacSMCutsceneLocations.METALIS_ESCAPE,         RACSMPLANET.METALIS,       False),  # Giant Clank disabled
    # Dreamtime
    (RacSMCutsceneLocations.DREAMTIME_COMPLETE,       RACSMPLANET.DREAMTIME,     False),
    # Outpost Omega
    (RacSMCutsceneLocations.OUTPOST_OMEGA,            RACSMPLANET.OUTPOST_OMEGA, True),
    (RacSMCutsceneLocations.OUTPOST_OMEGA_ESCAPE,     RACSMPLANET.OUTPOST_OMEGA, False),
    (RacSMCutsceneLocations.OUTPOST_OMEGA_REMATCH,    RACSMPLANET.OUTPOST_OMEGA, False),
    # Challax
    # (RacSMCutsceneLocations.METALIS_CLANK,          RACSMPLANET.CHALLAX,       True),   # Giant Clank disabled
    # (RacSMCutsceneLocations.CHALLAX_CLANK,          RACSMPLANET.CHALLAX,       False),  # Giant Clank disabled
    # Dayni Moon
    (RacSMCutsceneLocations.DAYNI_MOON,               RACSMPLANET.DAYNI_MOON,    False),
    (RacSMCutsceneLocations.DAYNI_MOON_FIGHT1,        RACSMPLANET.DAYNI_MOON,    True),
    (RacSMCutsceneLocations.DAYNI_MOON_FIGHT2,        RACSMPLANET.DAYNI_MOON,    True),
    (RacSMCutsceneLocations.DAYNI_MOON_LUNA,          RACSMPLANET.DAYNI_MOON,    False),
    # Inside Clank
    (RacSMCutsceneLocations.INSIDE_CLANK_ESCAPE,      RACSMPLANET.INSIDE_CLANK,  False),
    (RacSMCutsceneLocations.INSIDE_CLANK_TECHNOMITES, RACSMPLANET.INSIDE_CLANK,  False),
    # Quodrona
    (RacSMCutsceneLocations.QUODRONA_CLONE,           RACSMPLANET.QUODRONA,      True),
    (RacSMCutsceneLocations.QUODRONA_CHASE,           RACSMPLANET.QUODRONA,      True),
    (RacSMCutsceneLocations.QUODRONA_MECHA,           RACSMPLANET.QUODRONA,      True),
    (RacSMCutsceneLocations.QUODRONA_FIND,            RACSMPLANET.QUODRONA,      False),
    # Enter Planet (appended last so IDs above stay stable)
    (RacSMCutsceneLocations.POKITARU_ENTER,           RACSMPLANET.POKITARU,      True),
    (RacSMCutsceneLocations.RYLLUS_ENTER,             RACSMPLANET.RYLLUS,        True),
    (RacSMCutsceneLocations.KALIDON_ENTER,            RACSMPLANET.KALIDON,       True),
    (RacSMCutsceneLocations.METALIS_ENTER,            RACSMPLANET.METALIS,       True),
    (RacSMCutsceneLocations.DREAMTIME_ENTER,          RACSMPLANET.DREAMTIME,     True),
    (RacSMCutsceneLocations.OUTPOST_OMEGA_ENTER,      RACSMPLANET.OUTPOST_OMEGA, True),
    (RacSMCutsceneLocations.CHALLAX_ENTER,            RACSMPLANET.CHALLAX,       True),
    (RacSMCutsceneLocations.DAYNI_MOON_ENTER,         RACSMPLANET.DAYNI_MOON,    True),
    (RacSMCutsceneLocations.INSIDE_CLANK_ENTER,       RACSMPLANET.INSIDE_CLANK,  True),
    (RacSMCutsceneLocations.QUODRONA_ENTER,           RACSMPLANET.QUODRONA,      True),
]

STORY_MISSION_LOCATIONS: dict[str, RACLocationData] = {
    name: RACLocationData(BASE_ID + 3000 + idx, region)
    for idx, (name, region, is_cutscene) in enumerate(_MISSION_ENTRIES, start=1)
    if not is_cutscene
}

CUTSCENE_LOCATIONS: dict[str, RACLocationData] = {
    name: RACLocationData(BASE_ID + 3000 + idx, region)
    for idx, (name, region, is_cutscene) in enumerate(_MISSION_ENTRIES, start=1)
    if is_cutscene
}

# Union kept for ALL_LOCATIONS (full location pool) and any code still referencing this name.
MISSION_LOCATIONS: dict[str, RACLocationData] = {**STORY_MISSION_LOCATIONS, **CUTSCENE_LOCATIONS}

ALL_LOCATIONS: dict[str, RACLocationData] = {
    **TITANIUM_BOLT_LOCATIONS,
    **ARMOUR_PICKUP_LOCATIONS,
    **BOSS_LOCATIONS,
    **GADGET_PICKUP_LOCATIONS,
    **SKILL_POINT_LOCATIONS,
    **MISSION_LOCATIONS,
    **WEAPON_VENDOR_LOCATIONS,
    **GADGET_VENDOR_LOCATIONS,
    **WEAPON_MOD_VENDOR_LOCATIONS,
    **ARMOUR_SET_CHECK_LOCATIONS,
    **CHALLENGE_LOCATIONS,
    **ALL_CLANK_LOCATIONS,
    **SKYBOARD_ITEM_LOCATIONS,
    **EXTRA_SKYBOARD_LOCATIONS,
}

LOCATION_ID_TO_NAME: dict[int, str] = {data.code: name for name, data in ALL_LOCATIONS.items()}

# ── Vendor location ↔ internal-name lookup tables ─────────────────────────────
# Derived here so both the game-state layer and the client can share one source.

from .items import GADGET_DISPLAY_TO_INTERNAL, WEAPON_DISPLAY_TO_INTERNAL

# Map from vendor location name → internal weapon/gadget name
VENDOR_WEAPON_LOC: dict[str, str] = {
    RACSMVENDORLOCATION.POKITARU_LACERATOR:  WEAPON_DISPLAY_TO_INTERNAL["Lacerator"],
    RACSMVENDORLOCATION.POKITARU_ACID:       WEAPON_DISPLAY_TO_INTERNAL["Acid Bomb Glove"],
    RACSMVENDORLOCATION.POKITARU_CONCUSSION: WEAPON_DISPLAY_TO_INTERNAL["Concussion Gun"],
    RACSMVENDORLOCATION.RYLLUS_AGENTS:       WEAPON_DISPLAY_TO_INTERNAL["Agents of Doom"],
    RACSMVENDORLOCATION.KALIDON_SCORCHER:    WEAPON_DISPLAY_TO_INTERNAL["Scorcher"],
    RACSMVENDORLOCATION.DREAMTIME_SUCK:      WEAPON_DISPLAY_TO_INTERNAL["Suck Cannon"],
    RACSMVENDORLOCATION.OUTPOST_OMEGA_BEE:   WEAPON_DISPLAY_TO_INTERNAL["Bee Mine Glove"],
    RACSMVENDORLOCATION.CHALLAX_SNIPER:      WEAPON_DISPLAY_TO_INTERNAL["Sniper Mine"],
    RACSMVENDORLOCATION.DAYNI_MOON_SHOCK:    WEAPON_DISPLAY_TO_INTERNAL["Shock Rocket"],
    RACSMVENDORLOCATION.INSIDE_CLANK_STATIC: WEAPON_DISPLAY_TO_INTERNAL["Static Barrier"],
    RACSMVENDORLOCATION.QUODRONA_LASER:      WEAPON_DISPLAY_TO_INTERNAL["Laser Tracer"],
}

VENDOR_GADGET_LOC: dict[str, str] = {
    RACSMVENDORLOCATION.POKITARU_HYPERSHOT:      GADGET_DISPLAY_TO_INTERNAL["Hypershot"],
    RACSMVENDORLOCATION.CHALLAX_PDA:             GADGET_DISPLAY_TO_INTERNAL["PDA"],
    RACSMVENDORLOCATION.DAYNI_MOON_MAP:          GADGET_DISPLAY_TO_INTERNAL["Map-O-Matic"],
    RACSMVENDORLOCATION.CHALLAX_BOLT_GRABBER:    GADGET_DISPLAY_TO_INTERNAL["Bolt Grabber"],
    RACSMVENDORLOCATION.OUTPOST_OMEGA_BOX_BREAKER: GADGET_DISPLAY_TO_INTERNAL["Box Breaker"],
}

WEAPON_INTERNAL_TO_LOCATION: dict[str, str] = {v: k for k, v in VENDOR_WEAPON_LOC.items()}
GADGET_INTERNAL_TO_LOCATION: dict[str, str] = {v: k for k, v in VENDOR_GADGET_LOC.items()}

# (internal_weapon, 1-based game slot) → AP location name.
# Slot 1 = mod_slot_one, 2 = mod_slot_two, 3 = mod_slot_three in the weapon struct.
# Scorcher Spitfire is confirmed in slot 2; all others use the first available slot.
_MOD_SLOT_ASSIGNMENT: list[tuple[str, int, str]] = [
    ("lacerator",       2, RACSMVENDORLOCATION.KALIDON_LACERATOR_LOCK),
    ("lacerator",       1, RACSMVENDORLOCATION.CHALLAX_LACERATOR_DOUBLE),
    ("acid_bomb_glove", 1, RACSMVENDORLOCATION.CHALLAX_ACID_BURN),
    ("acid_bomb_glove", 2, RACSMVENDORLOCATION.CHALLAX_ACID_EPOXY),
    ("concussion_gun",  1, RACSMVENDORLOCATION.KALIDON_CONCUSSION_SPLIT),
    ("concussion_gun",  2, RACSMVENDORLOCATION.CHALLAX_CONCUSSION_LOCK),
    ("concussion_gun",  3, RACSMVENDORLOCATION.CHALLAX_CONCUSSION_CHARGE),
    ("bee_mine_glove",  1, RACSMVENDORLOCATION.CHALLAX_BEE_WORKER),
    ("agents_of_doom",  1, RACSMVENDORLOCATION.QUODRONA_AGENTS_LAUNCHER),
    ("scorcher",        2, RACSMVENDORLOCATION.QUODRONA_SCORCHER_SPITFIRE),
    ("sniper_mine",     1, RACSMVENDORLOCATION.QUODRONA_SNIPER_SPLIT),
    ("shock_rocket",    1, RACSMVENDORLOCATION.QUODRONA_SHOCK_LOCK),
    ("shock_rocket",    2, RACSMVENDORLOCATION.QUODRONA_SHOCK_AFTER),
]

_ATTR_NAMES = ("mod_slot_one", "mod_slot_two", "mod_slot_three")

# For WeaponState / HooksMixin: slot key matches struct field name ("mod_slot_one" etc.)
MOD_INTERNAL_TO_LOCATION: dict[tuple[str, str], str] = {
    (w, _ATTR_NAMES[i - 1]): loc for w, i, loc in _MOD_SLOT_ASSIGNMENT
}

# For VendorSession / VendorHandlerMixin: slot key matches _SLOT_NAMES ("one"/"two"/"three")
MOD_INTERNAL_TO_VENDOR_SLOT_LOCATION: dict[tuple[str, str], str] = {
    (w, ("one", "two", "three")[i - 1]): loc for w, i, loc in _MOD_SLOT_ASSIGNMENT
}

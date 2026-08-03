from typing import NamedTuple

from .constants import (
    Rac5ArmourSet,
    Rac5Locations,
    Rac5ModVendorLocations,
    Rac5Planets,
    Rac5SkyboardChallenges as RACSMSKY,
    Rac5VendorLocations,
    Rac5CutsceneLocations,
    Rac5WeaponKeys,
)
from .core.armour import ARMOUR_PICKUPS
from .core.locations.weapon_level_locations import WEAPON_LEVEL_NAMES
from .core.locations.challenge_locations import (
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
    Rac5Locations.QUODRONA_GOAL: RACLocationData(BASE_ID + 1200, Rac5Planets.QUODRONA),
}

WEAPON_VENDOR_LOCATIONS: dict[str, RACLocationData] = {
    Rac5VendorLocations.POKITARU_LACERATOR:  RACLocationData(BASE_ID + 2001, Rac5Planets.POKITARU),
    Rac5VendorLocations.POKITARU_ACID:       RACLocationData(BASE_ID + 2002, Rac5Planets.POKITARU),
    Rac5VendorLocations.POKITARU_CONCUSSION: RACLocationData(BASE_ID + 2003, Rac5Planets.POKITARU),
    Rac5VendorLocations.RYLLUS_AGENTS:       RACLocationData(BASE_ID + 2004, Rac5Planets.RYLLUS),
    Rac5VendorLocations.KALIDON_SCORCHER:    RACLocationData(BASE_ID + 2005, Rac5Planets.KALIDON),
    Rac5VendorLocations.DREAMTIME_SUCK:      RACLocationData(BASE_ID + 2006, Rac5Planets.DREAMTIME),
    Rac5VendorLocations.OUTPOST_OMEGA_BEE:   RACLocationData(BASE_ID + 2007, Rac5Planets.OUTPOST_OMEGA),
    Rac5VendorLocations.CHALLAX_SNIPER:      RACLocationData(BASE_ID + 2008, Rac5Planets.CHALLAX),
    Rac5VendorLocations.DAYNI_MOON_SHOCK:    RACLocationData(BASE_ID + 2009, Rac5Planets.DAYNI_MOON),
    Rac5VendorLocations.INSIDE_CLANK_STATIC: RACLocationData(BASE_ID + 2010, Rac5Planets.INSIDE_CLANK),
    Rac5VendorLocations.QUODRONA_LASER:      RACLocationData(BASE_ID + 2011, Rac5Planets.QUODRONA),
}

GADGET_VENDOR_LOCATIONS: dict[str, RACLocationData] = {
    Rac5VendorLocations.POKITARU_HYPERSHOT:      RACLocationData(BASE_ID + 2101, Rac5Planets.POKITARU),
    Rac5VendorLocations.CHALLAX_PDA:             RACLocationData(BASE_ID + 2102, Rac5Planets.CHALLAX),
    Rac5VendorLocations.DAYNI_MOON_MAP:          RACLocationData(BASE_ID + 2103, Rac5Planets.DAYNI_MOON),
    Rac5VendorLocations.CHALLAX_BOLT_GRABBER:    RACLocationData(BASE_ID + 2104, Rac5Planets.CHALLAX),
    Rac5VendorLocations.OUTPOST_OMEGA_BOX_BREAKER: RACLocationData(BASE_ID + 2105, Rac5Planets.OUTPOST_OMEGA),
}

WEAPON_MOD_VENDOR_LOCATIONS: dict[str, RACLocationData] = {
    Rac5ModVendorLocations.KALIDON_LACERATOR_LOCK:    RACLocationData(BASE_ID + 2202, Rac5Planets.KALIDON),
    Rac5ModVendorLocations.KALIDON_CONCUSSION_SPLIT:  RACLocationData(BASE_ID + 2205, Rac5Planets.KALIDON),
    Rac5ModVendorLocations.CHALLAX_LACERATOR_DOUBLE:  RACLocationData(BASE_ID + 2201, Rac5Planets.CHALLAX),
    Rac5ModVendorLocations.CHALLAX_ACID_BURN:         RACLocationData(BASE_ID + 2203, Rac5Planets.CHALLAX),
    Rac5ModVendorLocations.CHALLAX_ACID_EPOXY:        RACLocationData(BASE_ID + 2204, Rac5Planets.CHALLAX),
    Rac5ModVendorLocations.CHALLAX_CONCUSSION_LOCK:   RACLocationData(BASE_ID + 2206, Rac5Planets.CHALLAX),
    Rac5ModVendorLocations.CHALLAX_CONCUSSION_CHARGE: RACLocationData(BASE_ID + 2207, Rac5Planets.CHALLAX),
    Rac5ModVendorLocations.CHALLAX_BEE_WORKER:        RACLocationData(BASE_ID + 2211, Rac5Planets.CHALLAX),
    Rac5ModVendorLocations.QUODRONA_AGENTS_LAUNCHER:  RACLocationData(BASE_ID + 2209, Rac5Planets.QUODRONA),
    Rac5ModVendorLocations.QUODRONA_SCORCHER_SPITFIRE: RACLocationData(BASE_ID + 2210, Rac5Planets.QUODRONA),
    Rac5ModVendorLocations.QUODRONA_SNIPER_SPLIT:     RACLocationData(BASE_ID + 2212, Rac5Planets.QUODRONA),
    Rac5ModVendorLocations.QUODRONA_SHOCK_LOCK:       RACLocationData(BASE_ID + 2213, Rac5Planets.QUODRONA),
    Rac5ModVendorLocations.QUODRONA_SHOCK_AFTER:      RACLocationData(BASE_ID + 2214, Rac5Planets.QUODRONA),
}

# Weapon level locations — one per weapon per level (1-4, every weapon's max).
# Region is Pokitaru for all of them (same as ARMOUR_SET_CHECK_LOCATIONS
# below): leveling isn't tied to any one planet, just to owning the weapon
# and playing, so there's no more specific region to anchor it to.
from .core.weapons import WEAPON_DATA as _WEAPON_DATA

# (internal weapon key, 1-indexed level) -> AP location name. Used by the
# client to look up which location a newly-reached weapon level maps to.
# Level 1 is deliberately excluded: it's synonymous with owning the weapon
# at all (already covered by whatever location/item grants it), not a
# distinct in-game milestone, so it isn't modelled as a location here.
# Names come from WEAPON_LEVEL_NAMES (constants/weapon_levels.py) — an
# explicit mapping, not a dynamically-built getattr() lookup — so a typo/
# rename there is a KeyError at import time, not a silent lookup failure.
WEAPON_LEVEL_LOOKUP: dict[tuple[str, int], str] = {
    (internal, level): WEAPON_LEVEL_NAMES[internal][level]
    for internal, data in _WEAPON_DATA.items()
    for level in range(2, data.max_level + 1)
}

# Full universe of weapon level locations (levels 1 through each weapon's max),
# always present in ALL_LOCATIONS regardless of weapon_level_checks — same
# pattern as SKILL_POINT_LOCATIONS vs EASY_/HARD_SKILL_POINT_LOCATIONS.
WEAPON_LEVEL_LOCATIONS: dict[str, RACLocationData] = {
    loc_name: RACLocationData(BASE_ID + 5000 + idx, Rac5Planets.POKITARU)
    for idx, loc_name in enumerate(WEAPON_LEVEL_LOOKUP.values(), start=1)
}

# weapon_level_checks == max_level: only the "reached max level" check per weapon.
WEAPON_MAX_LEVEL_LOCATIONS: dict[str, RACLocationData] = {
    loc_name: WEAPON_LEVEL_LOCATIONS[loc_name]
    for (internal, level), loc_name in WEAPON_LEVEL_LOOKUP.items()
    if level == _WEAPON_DATA[internal].max_level
}

# weapon_level_checks == all: every other (non-max) level check, added on top
# of WEAPON_MAX_LEVEL_LOCATIONS so the two tables never overlap.
WEAPON_SUB_MAX_LEVEL_LOCATIONS: dict[str, RACLocationData] = {
    loc_name: data for loc_name, data in WEAPON_LEVEL_LOCATIONS.items()
    if loc_name not in WEAPON_MAX_LEVEL_LOCATIONS
}

from .core.locations.armour_set_locations import ARMOUR_SET_CHECKS

ARMOUR_SET_CHECK_LOCATIONS: dict[str, RACLocationData] = {
    name: RACLocationData(BASE_ID + 1500 + idx, Rac5Planets.POKITARU)
    for idx, name in enumerate(ARMOUR_SET_CHECKS, start=1)
}

# NG+ Items option (options.py's NgPlusItems): RYNO and the Chameleon/
# Hyperborean armour sets are New Game Plus exclusives in vanilla — with
# that option off, none of their items are ever placed (see world.py's
# create_items()/generate_basic()), so any location whose only
# reward/rule depends on them has to be excluded too. Single source of
# truth shared by regions.py (location creation) and rules/weapon_levels.py
# + rules/armour_sets.py (rule assignment) — both must agree on exactly
# what got created, or world.set_rule() ends up targeting a Location
# regions.py never actually built. Stalker/Ice II are included here even
# though they're not pure Chameleon/Hyperborean sets — both need one piece
# from the excluded set to ever be completed (see rules/armour_sets.py's
# _ARMOUR_SET_RULES).
NG_PLUS_WEAPON_LEVEL_LOCATIONS: frozenset[str] = frozenset(
    loc_name for (internal, _level), loc_name in WEAPON_LEVEL_LOOKUP.items()
    if internal == Rac5WeaponKeys.RYNO
)

NG_PLUS_ARMOUR_SET_LOCATIONS: frozenset[str] = frozenset({
    Rac5ArmourSet.HYPERBOREAN,
    Rac5ArmourSet.CHAMELEON,
    Rac5ArmourSet.ICE_II,
    Rac5ArmourSet.STALKER,
})

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
    Rac5Locations.RYLLUS_SPROUT:  RACLocationData(BASE_ID + 1401, Rac5Planets.RYLLUS),
    Rac5Locations.KALIDON_SHRINK: RACLocationData(BASE_ID + 1407, Rac5Planets.KALIDON),
    # Rac5Locations.METALIS_GLOVES: RACLocationData(BASE_ID + 1406, Rac5Planets.METALIS),  # Giant Clank disabled
}

SKYBOARD_ITEM_LOCATIONS: dict[str, RACLocationData] = {
    RACSMSKY.KALIDON_LEARNER:          RACLocationData(BASE_ID + 1402, Rac5Planets.KALIDON),
    RACSMSKY.KALIDON_MASTER:           RACLocationData(BASE_ID + 1405, Rac5Planets.KALIDON),
    RACSMSKY.OUTPOST_OMEGA_VERTIGO:    RACLocationData(BASE_ID + 1800, Rac5Planets.OUTPOST_OMEGA),
    RACSMSKY.OUTPOST_OMEGA_INTERIOR:   RACLocationData(BASE_ID + 1801, Rac5Planets.OUTPOST_OMEGA),
}

EXTRA_SKYBOARD_LOCATIONS: dict[str, RACLocationData] = {
    RACSMSKY.KALIDON_TICKET:           RACLocationData(BASE_ID + 1403, Rac5Planets.KALIDON),
    RACSMSKY.KALIDON_TRICKY:           RACLocationData(BASE_ID + 1404, Rac5Planets.KALIDON),
    RACSMSKY.OUTPOST_OMEGA_DANGER:     RACLocationData(BASE_ID + 1802, Rac5Planets.OUTPOST_OMEGA),
    RACSMSKY.OUTPOST_OMEGA_VORTEX:     RACLocationData(BASE_ID + 1803, Rac5Planets.OUTPOST_OMEGA),
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
    (Rac5CutsceneLocations.POKITARU_FIGHT,           Rac5Planets.POKITARU,      False),
    (Rac5CutsceneLocations.RYLLUS_BUZZING,           Rac5Planets.RYLLUS,        True),
    (Rac5CutsceneLocations.RYLLUS_ARTIFACT,          Rac5Planets.RYLLUS,        False),
    (Rac5CutsceneLocations.RYLLUS_TEMPLE,            Rac5Planets.RYLLUS,        False),
    (Rac5CutsceneLocations.KALIDON_EXPLORE,          Rac5Planets.KALIDON,       True),
    (Rac5CutsceneLocations.KALIDON_WIN,              Rac5Planets.KALIDON,       False),
    (Rac5CutsceneLocations.METALIS_WAR,              Rac5Planets.METALIS,       False),
    # (Rac5CutsceneLocations.METALIS_ESCAPE,         Rac5Planets.METALIS,       False),  # Giant Clank disabled
    (Rac5CutsceneLocations.DREAMTIME_COMPLETE,       Rac5Planets.DREAMTIME,     False),
    (Rac5CutsceneLocations.OUTPOST_OMEGA,            Rac5Planets.OUTPOST_OMEGA, True),
    (Rac5CutsceneLocations.OUTPOST_OMEGA_ESCAPE,     Rac5Planets.OUTPOST_OMEGA, False),
    (Rac5CutsceneLocations.OUTPOST_OMEGA_REMATCH,    Rac5Planets.OUTPOST_OMEGA, False),
    # (Rac5CutsceneLocations.METALIS_CLANK,          Rac5Planets.CHALLAX,       True),   # Giant Clank disabled
    # (Rac5CutsceneLocations.CHALLAX_CLANK,          Rac5Planets.CHALLAX,       False),  # Giant Clank disabled
    (Rac5CutsceneLocations.DAYNI_MOON,               Rac5Planets.DAYNI_MOON,    False),
    (Rac5CutsceneLocations.DAYNI_MOON_FIGHT1,        Rac5Planets.DAYNI_MOON,    True),
    (Rac5CutsceneLocations.DAYNI_MOON_FIGHT2,        Rac5Planets.DAYNI_MOON,    True),
    (Rac5CutsceneLocations.DAYNI_MOON_LUNA,          Rac5Planets.DAYNI_MOON,    False),
    (Rac5CutsceneLocations.INSIDE_CLANK_ESCAPE,      Rac5Planets.INSIDE_CLANK,  False),
    (Rac5CutsceneLocations.INSIDE_CLANK_TECHNOMITES, Rac5Planets.INSIDE_CLANK,  False),
    (Rac5CutsceneLocations.QUODRONA_CLONE,           Rac5Planets.QUODRONA,      True),
    (Rac5CutsceneLocations.QUODRONA_CHASE,           Rac5Planets.QUODRONA,      True),
    (Rac5CutsceneLocations.QUODRONA_MECHA,           Rac5Planets.QUODRONA,      True),
    (Rac5CutsceneLocations.QUODRONA_FIND,            Rac5Planets.QUODRONA,      False),
    # Enter Planet (appended last so IDs above stay stable)
    (Rac5CutsceneLocations.POKITARU_ENTER,           Rac5Planets.POKITARU,      True),
    (Rac5CutsceneLocations.RYLLUS_ENTER,             Rac5Planets.RYLLUS,        True),
    (Rac5CutsceneLocations.KALIDON_ENTER,            Rac5Planets.KALIDON,       True),
    (Rac5CutsceneLocations.METALIS_ENTER,            Rac5Planets.METALIS,       True),
    (Rac5CutsceneLocations.DREAMTIME_ENTER,          Rac5Planets.DREAMTIME,     True),
    (Rac5CutsceneLocations.OUTPOST_OMEGA_ENTER,      Rac5Planets.OUTPOST_OMEGA, True),
    (Rac5CutsceneLocations.CHALLAX_ENTER,            Rac5Planets.CHALLAX,       True),

    (Rac5CutsceneLocations.INSIDE_CLANK_ENTER,       Rac5Planets.INSIDE_CLANK,  True),
    (Rac5CutsceneLocations.QUODRONA_ENTER,           Rac5Planets.QUODRONA,      True),

    # New locations appended here (same ID-stability reasoning as Enter Planet above).
    (Rac5CutsceneLocations.DREAMTIME_SLEEPING_RATCHET, Rac5Planets.DREAMTIME,   True),
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
    **WEAPON_LEVEL_LOCATIONS,
    **ARMOUR_SET_CHECK_LOCATIONS,
    **CHALLENGE_LOCATIONS,
    **ALL_CLANK_LOCATIONS,
    **SKYBOARD_ITEM_LOCATIONS,
    **EXTRA_SKYBOARD_LOCATIONS,
}

LOCATION_ID_TO_NAME: dict[int, str] = {data.code: name for name, data in ALL_LOCATIONS.items()}

# Vendor location ↔ internal-name lookup tables
# Derived here so both the game-state layer and the client can share one source.

from .items import GADGET_DISPLAY_TO_INTERNAL, WEAPON_DISPLAY_TO_INTERNAL

# Map from vendor location name → internal weapon/gadget name
VENDOR_WEAPON_LOC: dict[str, str] = {
    Rac5VendorLocations.POKITARU_LACERATOR:  WEAPON_DISPLAY_TO_INTERNAL["Lacerator"],
    Rac5VendorLocations.POKITARU_ACID:       WEAPON_DISPLAY_TO_INTERNAL["Acid Bomb Glove"],
    Rac5VendorLocations.POKITARU_CONCUSSION: WEAPON_DISPLAY_TO_INTERNAL["Concussion Gun"],
    Rac5VendorLocations.RYLLUS_AGENTS:       WEAPON_DISPLAY_TO_INTERNAL["Agents of Doom"],
    Rac5VendorLocations.KALIDON_SCORCHER:    WEAPON_DISPLAY_TO_INTERNAL["Scorcher"],
    Rac5VendorLocations.DREAMTIME_SUCK:      WEAPON_DISPLAY_TO_INTERNAL["Suck Cannon"],
    Rac5VendorLocations.OUTPOST_OMEGA_BEE:   WEAPON_DISPLAY_TO_INTERNAL["Bee Mine Glove"],
    Rac5VendorLocations.CHALLAX_SNIPER:      WEAPON_DISPLAY_TO_INTERNAL["Sniper Mine"],
    Rac5VendorLocations.DAYNI_MOON_SHOCK:    WEAPON_DISPLAY_TO_INTERNAL["Shock Rocket"],
    Rac5VendorLocations.INSIDE_CLANK_STATIC: WEAPON_DISPLAY_TO_INTERNAL["Static Barrier"],
    Rac5VendorLocations.QUODRONA_LASER:      WEAPON_DISPLAY_TO_INTERNAL["Laser Tracer"],
}

VENDOR_GADGET_LOC: dict[str, str] = {
    Rac5VendorLocations.POKITARU_HYPERSHOT:      GADGET_DISPLAY_TO_INTERNAL["Hypershot"],
    Rac5VendorLocations.CHALLAX_PDA:             GADGET_DISPLAY_TO_INTERNAL["PDA"],
    Rac5VendorLocations.DAYNI_MOON_MAP:          GADGET_DISPLAY_TO_INTERNAL["Map-O-Matic"],
    Rac5VendorLocations.CHALLAX_BOLT_GRABBER:    GADGET_DISPLAY_TO_INTERNAL["Bolt Grabber"],
    Rac5VendorLocations.OUTPOST_OMEGA_BOX_BREAKER: GADGET_DISPLAY_TO_INTERNAL["Box Breaker"],
}

WEAPON_INTERNAL_TO_LOCATION: dict[str, str] = {v: k for k, v in VENDOR_WEAPON_LOC.items()}
GADGET_INTERNAL_TO_LOCATION: dict[str, str] = {v: k for k, v in VENDOR_GADGET_LOC.items()}

# (internal_weapon, 1-based game slot) → AP location name.
# Slot 1 = mod_slot_one, 2 = mod_slot_two, 3 = mod_slot_three in the weapon struct.
# Scorcher Spitfire is confirmed in slot 2; all others use the first available slot.
_MOD_SLOT_ASSIGNMENT: list[tuple[str, int, str]] = [
    ("lacerator",       2, Rac5ModVendorLocations.KALIDON_LACERATOR_LOCK),
    ("lacerator",       1, Rac5ModVendorLocations.CHALLAX_LACERATOR_DOUBLE),
    ("acid_bomb_glove", 1, Rac5ModVendorLocations.CHALLAX_ACID_BURN),
    ("acid_bomb_glove", 2, Rac5ModVendorLocations.CHALLAX_ACID_EPOXY),
    ("concussion_gun",  1, Rac5ModVendorLocations.KALIDON_CONCUSSION_SPLIT),
    ("concussion_gun",  3, Rac5ModVendorLocations.CHALLAX_CONCUSSION_LOCK),
    ("concussion_gun",  2, Rac5ModVendorLocations.CHALLAX_CONCUSSION_CHARGE),
    ("bee_mine_glove",  1, Rac5ModVendorLocations.CHALLAX_BEE_WORKER),
    ("agents_of_doom",  2, Rac5ModVendorLocations.QUODRONA_AGENTS_LAUNCHER),
    ("scorcher",        2, Rac5ModVendorLocations.QUODRONA_SCORCHER_SPITFIRE),
    ("sniper_mine",     1, Rac5ModVendorLocations.QUODRONA_SNIPER_SPLIT),
    ("shock_rocket",    3, Rac5ModVendorLocations.QUODRONA_SHOCK_LOCK),
    ("shock_rocket",    1, Rac5ModVendorLocations.QUODRONA_SHOCK_AFTER),
]

_ATTR_NAMES = ("mod_slot_one", "mod_slot_two", "mod_slot_three")

# For WeaponInventory.set_mod(): slot key matches struct field name ("mod_slot_one" etc.)
MOD_INTERNAL_TO_LOCATION: dict[tuple[str, str], str] = {
    (w, _ATTR_NAMES[i - 1]): loc for w, i, loc in _MOD_SLOT_ASSIGNMENT
}

# For VendorSession / VendorHandlerMixin: slot key matches _SLOT_NAMES ("one"/"two"/"three")
MOD_INTERNAL_TO_VENDOR_SLOT_LOCATION: dict[tuple[str, str], str] = {
    (w, ("one", "two", "three")[i - 1]): loc for w, i, loc in _MOD_SLOT_ASSIGNMENT
}

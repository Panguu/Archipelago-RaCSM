from typing import NamedTuple

from ..constants import (
    Rac5ArmourSet,
    Rac5CutsceneLocations,
    Rac5Locations,
    Rac5ModVendorLocations,
    Rac5NanotechLevels,
    Rac5Planets,
    Rac5SkillPoints,
    Rac5SkyboardChallenges,
    Rac5TitanVendorLocations,
    Rac5VendorLocations,
    Rac5WeaponKeys,
)
from ..core.armour import ARMOUR_PICKUPS
from ..core.locations.challenge_locations import (
    CHALLENGE_GROUP_DERBY,
    CHALLENGE_GROUP_GADGETBOT,
    CHALLENGE_GROUP_GADGETBOT_TOSS,
    CHALLENGE_NAME_TO_GROUP,
    CHALLENGE_PICKUPS,
    DERBY_CLANK_PICKUPS,
    GADGETBOT_CLANK_PICKUPS,
    GADGETBOT_TOSS_CLANK_PICKUPS,
)
from ..core.locations.weapon_level_locations import WEAPON_LEVEL_NAMES
from ..core.shrink_ray import SHRINK_RAY_SKIP_LOCATION_NAMES
from ..core.skill_points import (
    CLANK_CHALLENGE_SKILL_POINTS,
    HARD_SKILL_POINTS,
    SKILL_POINTS,
    SKYBOARD_CHALLENGE_SKILL_POINTS,
)
from ..core.titanium_bolts import TITANIUM_BOLTS
from ..core.weapons import WEAPON_DATA as _WEAPON_DATA
from ..core.locations.armour_set_locations import ARMOUR_SET_CHECKS
from ..items import GADGET_DISPLAY_TO_INTERNAL, WEAPON_DISPLAY_TO_INTERNAL

BASE_ID = 77_700_000


class RACLocationData(NamedTuple):
    code: int
    region: str


# --- ID assignment -----------------------------------------------------
#
# Every location gets a numeric AP id, laid out in fixed-size blocks: one
# block per planet (in PLANET_ORDER), plus one trailing "shared" block for
# locations that aren't really tied to a single planet (weapon levels,
# nanotech levels, armour-set-combo checks — all anchored to Pokitaru only
# because the AP region graph needs *some* region, not because they belong
# there). IDs are free to be renumbered (no live seeds depend on the old
# numbering), so blocks are sized generously (300 slots) — comfortably more
# than any planet's real location count, leaving well over the requested
# 20-id buffer before the next block starts.
PLANET_ORDER: tuple[str, ...] = (
    Rac5Planets.POKITARU,
    Rac5Planets.RYLLUS,
    Rac5Planets.KALIDON,
    Rac5Planets.METALIS,
    Rac5Planets.DREAMTIME,
    Rac5Planets.OUTPOST_OMEGA,
    Rac5Planets.CHALLAX,
    Rac5Planets.DAYNI_MOON,
    Rac5Planets.INSIDE_CLANK,
    Rac5Planets.QUODRONA,
)

_PLANET_BLOCK_SIZE = 300
_PLANET_BLOCK_BASE: dict[str, int] = {
    planet: BASE_ID + i * _PLANET_BLOCK_SIZE for i, planet in enumerate(PLANET_ORDER)
}
_SHARED_BLOCK_BASE = BASE_ID + len(PLANET_ORDER) * _PLANET_BLOCK_SIZE

_planet_counters: dict[str, int] = dict.fromkeys(PLANET_ORDER, 0)
_shared_counter = 0


def _planet_id(region: str) -> int:
    """Next id in `region`'s block. Raises KeyError for a region not in PLANET_ORDER —
    every planet-scoped location's region must be a real planet."""
    _planet_counters[region] += 1
    return _PLANET_BLOCK_BASE[region] + _planet_counters[region]


def _shared_id() -> int:
    """Next id in the trailing shared block, for locations not tied to one planet."""
    global _shared_counter
    _shared_counter += 1
    return _SHARED_BLOCK_BASE + _shared_counter


TITANIUM_BOLT_LOCATIONS: dict[str, RACLocationData] = {
    name: RACLocationData(_planet_id(bolt.region), bolt.region)
    for name, bolt in TITANIUM_BOLTS.items()
}

ARMOUR_PICKUP_LOCATIONS: dict[str, RACLocationData] = {
    ap.name: RACLocationData(_planet_id(ap.planet), ap.planet)
    for ap in ARMOUR_PICKUPS
}


BOSS_LOCATIONS: dict[str, RACLocationData] = {
    Rac5Locations.QUODRONA_GOAL: RACLocationData(_planet_id(Rac5Planets.QUODRONA), Rac5Planets.QUODRONA),
}

WEAPON_VENDOR_LOCATIONS: dict[str, RACLocationData] = {
    Rac5VendorLocations.POKITARU_LACERATOR:  RACLocationData(_planet_id(Rac5Planets.POKITARU), Rac5Planets.POKITARU),
    Rac5VendorLocations.POKITARU_ACID:       RACLocationData(_planet_id(Rac5Planets.POKITARU), Rac5Planets.POKITARU),
    Rac5VendorLocations.POKITARU_CONCUSSION: RACLocationData(_planet_id(Rac5Planets.POKITARU), Rac5Planets.POKITARU),
    Rac5VendorLocations.RYLLUS_AGENTS:       RACLocationData(_planet_id(Rac5Planets.RYLLUS), Rac5Planets.RYLLUS),
    Rac5VendorLocations.KALIDON_SCORCHER:    RACLocationData(_planet_id(Rac5Planets.KALIDON), Rac5Planets.KALIDON),
    Rac5VendorLocations.DREAMTIME_SUCK:      RACLocationData(_planet_id(Rac5Planets.DREAMTIME), Rac5Planets.DREAMTIME),
    Rac5VendorLocations.OUTPOST_OMEGA_BEE:   RACLocationData(_planet_id(Rac5Planets.OUTPOST_OMEGA), Rac5Planets.OUTPOST_OMEGA),
    Rac5VendorLocations.CHALLAX_SNIPER:      RACLocationData(_planet_id(Rac5Planets.CHALLAX), Rac5Planets.CHALLAX),
    Rac5VendorLocations.DAYNI_MOON_SHOCK:    RACLocationData(_planet_id(Rac5Planets.DAYNI_MOON), Rac5Planets.DAYNI_MOON),
    Rac5VendorLocations.INSIDE_CLANK_STATIC: RACLocationData(_planet_id(Rac5Planets.INSIDE_CLANK), Rac5Planets.INSIDE_CLANK),
    Rac5VendorLocations.QUODRONA_LASER:      RACLocationData(_planet_id(Rac5Planets.QUODRONA), Rac5Planets.QUODRONA),
    # Challenge Mode 1+ only — RYNO has no vendor listing in vanilla.
    Rac5VendorLocations.POKITARU_RYNO:       RACLocationData(_planet_id(Rac5Planets.POKITARU), Rac5Planets.POKITARU),
}

GADGET_VENDOR_LOCATIONS: dict[str, RACLocationData] = {
    Rac5VendorLocations.POKITARU_HYPERSHOT:      RACLocationData(_planet_id(Rac5Planets.POKITARU), Rac5Planets.POKITARU),
    Rac5VendorLocations.CHALLAX_PDA:             RACLocationData(_planet_id(Rac5Planets.CHALLAX), Rac5Planets.CHALLAX),
    Rac5VendorLocations.DAYNI_MOON_MAP:          RACLocationData(_planet_id(Rac5Planets.DAYNI_MOON), Rac5Planets.DAYNI_MOON),
    Rac5VendorLocations.CHALLAX_BOLT_GRABBER:    RACLocationData(_planet_id(Rac5Planets.CHALLAX), Rac5Planets.CHALLAX),
    Rac5VendorLocations.OUTPOST_OMEGA_BOX_BREAKER: RACLocationData(_planet_id(Rac5Planets.OUTPOST_OMEGA), Rac5Planets.OUTPOST_OMEGA),
}

WEAPON_MOD_VENDOR_LOCATIONS: dict[str, RACLocationData] = {
    Rac5ModVendorLocations.KALIDON_LACERATOR_LOCK:    RACLocationData(_planet_id(Rac5Planets.KALIDON), Rac5Planets.KALIDON),
    Rac5ModVendorLocations.KALIDON_CONCUSSION_SPLIT:  RACLocationData(_planet_id(Rac5Planets.KALIDON), Rac5Planets.KALIDON),
    Rac5ModVendorLocations.CHALLAX_LACERATOR_DOUBLE:  RACLocationData(_planet_id(Rac5Planets.CHALLAX), Rac5Planets.CHALLAX),
    Rac5ModVendorLocations.CHALLAX_ACID_BURN:         RACLocationData(_planet_id(Rac5Planets.CHALLAX), Rac5Planets.CHALLAX),
    Rac5ModVendorLocations.CHALLAX_ACID_EPOXY:        RACLocationData(_planet_id(Rac5Planets.CHALLAX), Rac5Planets.CHALLAX),
    Rac5ModVendorLocations.CHALLAX_CONCUSSION_LOCK:   RACLocationData(_planet_id(Rac5Planets.CHALLAX), Rac5Planets.CHALLAX),
    Rac5ModVendorLocations.CHALLAX_CONCUSSION_CHARGE: RACLocationData(_planet_id(Rac5Planets.CHALLAX), Rac5Planets.CHALLAX),
    Rac5ModVendorLocations.CHALLAX_BEE_WORKER:        RACLocationData(_planet_id(Rac5Planets.CHALLAX), Rac5Planets.CHALLAX),
    Rac5ModVendorLocations.QUODRONA_AGENTS_LAUNCHER:  RACLocationData(_planet_id(Rac5Planets.QUODRONA), Rac5Planets.QUODRONA),
    Rac5ModVendorLocations.QUODRONA_SCORCHER_SPITFIRE: RACLocationData(_planet_id(Rac5Planets.QUODRONA), Rac5Planets.QUODRONA),
    Rac5ModVendorLocations.QUODRONA_SNIPER_SPLIT:     RACLocationData(_planet_id(Rac5Planets.QUODRONA), Rac5Planets.QUODRONA),
    Rac5ModVendorLocations.QUODRONA_SHOCK_LOCK:       RACLocationData(_planet_id(Rac5Planets.QUODRONA), Rac5Planets.QUODRONA),
    Rac5ModVendorLocations.QUODRONA_SHOCK_AFTER:      RACLocationData(_planet_id(Rac5Planets.QUODRONA), Rac5Planets.QUODRONA),
    # Challenge Mode 1+ only.
    Rac5ModVendorLocations.KALIDON_AGENTS_EXPLOSIVE:      RACLocationData(_planet_id(Rac5Planets.KALIDON), Rac5Planets.KALIDON),
    Rac5ModVendorLocations.KALIDON_SCORCHER_SUNFLARE:     RACLocationData(_planet_id(Rac5Planets.KALIDON), Rac5Planets.KALIDON),
    Rac5ModVendorLocations.KALIDON_SUCK_CANNON_BOUNCE:    RACLocationData(_planet_id(Rac5Planets.KALIDON), Rac5Planets.KALIDON),
    Rac5ModVendorLocations.KALIDON_BEE_HIVE_BOMB:         RACLocationData(_planet_id(Rac5Planets.KALIDON), Rac5Planets.KALIDON),
    Rac5ModVendorLocations.CHALLAX_SNIPER_SMART_REFLECTOR: RACLocationData(_planet_id(Rac5Planets.CHALLAX), Rac5Planets.CHALLAX),
    Rac5ModVendorLocations.CHALLAX_SHOCK_MULTI_LAUNCHER:  RACLocationData(_planet_id(Rac5Planets.CHALLAX), Rac5Planets.CHALLAX),
    Rac5ModVendorLocations.KALIDON_STATIC_REFLECTION:     RACLocationData(_planet_id(Rac5Planets.KALIDON), Rac5Planets.KALIDON),
    Rac5ModVendorLocations.QUODRONA_STATIC_MIRAGE:        RACLocationData(_planet_id(Rac5Planets.QUODRONA), Rac5Planets.QUODRONA),
    Rac5ModVendorLocations.CHALLAX_LASER_PIERCE:          RACLocationData(_planet_id(Rac5Planets.CHALLAX), Rac5Planets.CHALLAX),
    Rac5ModVendorLocations.QUODRONA_LASER_RICOCHET:       RACLocationData(_planet_id(Rac5Planets.QUODRONA), Rac5Planets.QUODRONA),
}

# Challenge Mode 1+ only — Titan variant purchases, one per weapon except
# RYNO (no Titan variant). Buying one floors that weapon's level at 5 and
# opens leveling up to 8 (see core/weapons.py's apply_progressive_leveling).
WEAPON_TITAN_VENDOR_LOCATIONS: dict[str, RACLocationData] = {
    Rac5TitanVendorLocations.POKITARU_LACERATOR_TITAN:   RACLocationData(_planet_id(Rac5Planets.POKITARU), Rac5Planets.POKITARU),
    Rac5TitanVendorLocations.POKITARU_ACID_TITAN:         RACLocationData(_planet_id(Rac5Planets.POKITARU), Rac5Planets.POKITARU),
    Rac5TitanVendorLocations.POKITARU_CONCUSSION_TITAN:   RACLocationData(_planet_id(Rac5Planets.POKITARU), Rac5Planets.POKITARU),
    Rac5TitanVendorLocations.RYLLUS_AGENTS_TITAN:         RACLocationData(_planet_id(Rac5Planets.RYLLUS), Rac5Planets.RYLLUS),
    Rac5TitanVendorLocations.KALIDON_SCORCHER_TITAN:      RACLocationData(_planet_id(Rac5Planets.KALIDON), Rac5Planets.KALIDON),
    Rac5TitanVendorLocations.DREAMTIME_SUCK_TITAN:        RACLocationData(_planet_id(Rac5Planets.DREAMTIME), Rac5Planets.DREAMTIME),
    Rac5TitanVendorLocations.OUTPOST_OMEGA_BEE_TITAN:     RACLocationData(_planet_id(Rac5Planets.OUTPOST_OMEGA), Rac5Planets.OUTPOST_OMEGA),
    Rac5TitanVendorLocations.CHALLAX_SNIPER_TITAN:        RACLocationData(_planet_id(Rac5Planets.CHALLAX), Rac5Planets.CHALLAX),
    Rac5TitanVendorLocations.DAYNI_MOON_MOOTATOR_TITAN:   RACLocationData(_planet_id(Rac5Planets.DAYNI_MOON), Rac5Planets.DAYNI_MOON),
    Rac5TitanVendorLocations.DAYNI_MOON_SHOCK_TITAN:      RACLocationData(_planet_id(Rac5Planets.DAYNI_MOON), Rac5Planets.DAYNI_MOON),
    Rac5TitanVendorLocations.INSIDE_CLANK_STATIC_TITAN:   RACLocationData(_planet_id(Rac5Planets.INSIDE_CLANK), Rac5Planets.INSIDE_CLANK),
    Rac5TitanVendorLocations.QUODRONA_LASER_TITAN:        RACLocationData(_planet_id(Rac5Planets.QUODRONA), Rac5Planets.QUODRONA),
}

# Weapon level locations — one per weapon per level (1-4, every weapon's max).
# Region is Pokitaru for all of them (same as ARMOUR_SET_CHECK_LOCATIONS
# below): leveling isn't tied to any one planet, just to owning the weapon
# and playing, so there's no more specific region to anchor it to. IDs come
# from the shared block, not Pokitaru's, since these aren't really Pokitaru
# locations.
# (internal weapon key, 1-indexed level) -> AP location name. Level 1 is
# excluded since it's synonymous with owning the weapon, not a distinct
# milestone. Sourced from WEAPON_LEVEL_NAMES so a typo/rename there is a
# KeyError at import time rather than a silent lookup failure.
WEAPON_LEVEL_LOOKUP: dict[tuple[str, int], str] = {
    (internal, level): WEAPON_LEVEL_NAMES[internal][level]
    for internal, data in _WEAPON_DATA.items()
    for level in range(2, data.max_level + 1)
}

# Full universe of weapon level locations (levels 1 through each weapon's max),
# always present in ALL_LOCATIONS regardless of weapon_level_checks — same
# pattern as SKILL_POINT_LOCATIONS vs EASY_/HARD_SKILL_POINT_LOCATIONS.
WEAPON_LEVEL_LOCATIONS: dict[str, RACLocationData] = {
    loc_name: RACLocationData(_shared_id(), Rac5Planets.POKITARU)
    for loc_name in WEAPON_LEVEL_LOOKUP.values()
}

# weapon_level_checks == max_level: only the "reached max level" check per
# weapon. Fixed at level 4 (the true vanilla max for every weapon, RYNO
# included) rather than _WEAPON_DATA[internal].max_level — that field is 8
# for Challenge Mode's Titan-extended weapons, but "max_level" here still
# means the pre-Challenge-Mode vanilla cap; levels 5-8 are their own
# separate Challenge-Mode-gated tier (see CHALLENGE_MODE_WEAPON_LEVEL_LOCATIONS
# below), not folded into this option.
WEAPON_MAX_LEVEL_LOCATIONS: dict[str, RACLocationData] = {
    loc_name: WEAPON_LEVEL_LOCATIONS[loc_name]
    for (_internal, level), loc_name in WEAPON_LEVEL_LOOKUP.items()
    if level == 4
}

# weapon_level_checks == all: every other non-max, non-Challenge-Mode level
# check (2-3), added on top of WEAPON_MAX_LEVEL_LOCATIONS so the two tables
# never overlap.
WEAPON_SUB_MAX_LEVEL_LOCATIONS: dict[str, RACLocationData] = {
    loc_name: WEAPON_LEVEL_LOCATIONS[loc_name]
    for (_internal, level), loc_name in WEAPON_LEVEL_LOOKUP.items()
    if level in (2, 3)
}

# Nanotech Level locations — one per level, 6 through 75 (levels 1-5 aren't
# locations; the player starts at level 5, see constants/nanotech_levels.py).
# Region is Pokitaru, same reasoning as weapon levels above: leveling isn't
# tied to any one planet.
NANOTECH_LEVEL_LOOKUP: dict[int, str] = {
    level: getattr(Rac5NanotechLevels, f"LEVEL_{level}")
    for level in range(6, 76)
}

NANOTECH_LEVEL_LOCATIONS: dict[str, RACLocationData] = {
    loc_name: RACLocationData(_shared_id(), Rac5Planets.POKITARU)
    for loc_name in NANOTECH_LEVEL_LOOKUP.values()
}


def nanotech_level_locations_for(interval: int, max_level: int) -> dict[str, RACLocationData]:
    """Subset of NANOTECH_LEVEL_LOCATIONS for the NanotechLevelInterval +
    NanotechLevelMax options: every level in NANOTECH_LEVEL_LOOKUP (6-75)
    that's both a multiple of `interval` and no higher than `max_level`.
    Empty (feature off) when interval <= 0. Shared by regions.py (creation)
    and rules/nanotech_levels.py (rule assignment) — both must agree."""
    if interval <= 0:
        return {}
    return {
        loc_name: NANOTECH_LEVEL_LOCATIONS[loc_name]
        for level, loc_name in NANOTECH_LEVEL_LOOKUP.items()
        if level % interval == 0 and level <= max_level
    }

ARMOUR_SET_CHECK_LOCATIONS: dict[str, RACLocationData] = {
    name: RACLocationData(_shared_id(), Rac5Planets.POKITARU)
    for name in ARMOUR_SET_CHECKS
}

# NG+ Items option: with it off, RYNO and Chameleon/Hyperborean items are
# never placed, so locations depending on them must be excluded too. Shared
# by regions.py (creation) and rules/weapon_levels.py + rules/armour_sets.py
# (rule assignment) — both must agree on the same exclusion. Stalker/Ice II
# are included since each needs one piece from the excluded sets.
NG_PLUS_WEAPON_LEVEL_LOCATIONS: frozenset[str] = frozenset(
    loc_name for (internal, _level), loc_name in WEAPON_LEVEL_LOOKUP.items()
    if internal == Rac5WeaponKeys.RYNO
)

# Levels 5-8 (Challenge Mode Titan variant) — gated on both NG+ Items and
# Challenge Mode 1+, same as CHALLENGE_MODE_1_ARMOUR_LOCATIONS etc. above.
# Split the same way as WEAPON_MAX_LEVEL_LOCATIONS/WEAPON_SUB_MAX_LEVEL_LOCATIONS:
# level 8 gates on weapon_level_checks >= 1 (mirrors "reached max level"),
# levels 5-7 gate on weapon_level_checks >= 2 (mirrors "every other level").
# Shared by regions.py (creation) and rules/weapon_levels.py (rule
# assignment) — both must agree on the same sets.
CHALLENGE_MODE_MAX_LEVEL_LOCATIONS: dict[str, RACLocationData] = {
    loc_name: WEAPON_LEVEL_LOCATIONS[loc_name]
    for (_internal, level), loc_name in WEAPON_LEVEL_LOOKUP.items()
    if level == 8
}

CHALLENGE_MODE_SUB_MAX_LEVEL_LOCATIONS: dict[str, RACLocationData] = {
    loc_name: WEAPON_LEVEL_LOCATIONS[loc_name]
    for (_internal, level), loc_name in WEAPON_LEVEL_LOOKUP.items()
    if level in (5, 6, 7)
}

CHALLENGE_MODE_WEAPON_LEVEL_LOCATIONS: frozenset[str] = frozenset(
    {*CHALLENGE_MODE_MAX_LEVEL_LOCATIONS, *CHALLENGE_MODE_SUB_MAX_LEVEL_LOCATIONS}
)

NG_PLUS_ARMOUR_SET_LOCATIONS: frozenset[str] = frozenset({
    Rac5ArmourSet.HYPERBOREAN,
    Rac5ArmourSet.CHAMELEON,
    Rac5ArmourSet.ICE_II,
    Rac5ArmourSet.STALKER,
})

# Challenge Mode option: locations that only exist at tier 1+ / tier 2. All of
# these are also still gated on NG+ Items being on (same as RYNO/Hyperborean/
# Chameleon/these same mods being in the item pool at all — see items.py's
# NG_PLUS_WEAPONS/NG_PLUS_ARMOUR_SETS/NG_PLUS_WEAPON_MODS). Shared by
# regions.py (creation) and rules/challenge_mode.py (rule assignment) — both
# must agree on the same sets.
CHALLENGE_MODE_1_ARMOUR_LOCATIONS: frozenset[str] = frozenset({
    Rac5Locations.POKITARU_HYPERBOREAN_GLOVES,
    Rac5Locations.RYLLUS_HYPERBOREAN_BOOTS,
    Rac5Locations.DREAMTIME_HYPERBOREAN_CHESTPLATE,
    Rac5Locations.CHALLAX_HYPERBOREAN_HELMET,
})

CHALLENGE_MODE_2_ARMOUR_LOCATIONS: frozenset[str] = frozenset({
    Rac5Locations.POKITARU_CHAMELEON_BOOTS,
    Rac5Locations.KALIDON_CHAMELEON_CHESTPLATE,
    Rac5Locations.OUTPOST_OMEGA_CHAMELEON_GLOVES,
    Rac5Locations.INSIDE_CLANK_CHAMELEON_HELMET,
})

CHALLENGE_MODE_RYNO_LOCATION: frozenset[str] = frozenset({Rac5VendorLocations.POKITARU_RYNO})

CHALLENGE_MODE_MOD_LOCATIONS: frozenset[str] = frozenset({
    Rac5ModVendorLocations.KALIDON_AGENTS_EXPLOSIVE,
    Rac5ModVendorLocations.KALIDON_SCORCHER_SUNFLARE,
    Rac5ModVendorLocations.KALIDON_SUCK_CANNON_BOUNCE,
    Rac5ModVendorLocations.KALIDON_BEE_HIVE_BOMB,
    Rac5ModVendorLocations.CHALLAX_SNIPER_SMART_REFLECTOR,
    Rac5ModVendorLocations.CHALLAX_SHOCK_MULTI_LAUNCHER,
    Rac5ModVendorLocations.KALIDON_STATIC_REFLECTION,
    Rac5ModVendorLocations.QUODRONA_STATIC_MIRAGE,
    Rac5ModVendorLocations.CHALLAX_LASER_PIERCE,
    Rac5ModVendorLocations.QUODRONA_LASER_RICOCHET,
})

# Giant Clank option: with it off, both sequences are locked out entirely
# (see PlanetInventory.giant_clank_allowed) so these must never be created
# as locations. Shared by regions.py (creation) and rules/metalis.py +
# rules/challax.py (rule assignment) — both must agree on the same exclusion.
GIANT_CLANK_LOCATIONS: frozenset[str] = frozenset({
    Rac5CutsceneLocations.METALIS_ESCAPE,
    Rac5Locations.METALIS_GLOVES,
    Rac5CutsceneLocations.CHALLAX_CLANK,
    Rac5Locations.CHALLAX_CHESTPLATE,
    Rac5SkillPoints.METALIS_TERROR,
    Rac5SkillPoints.CHALLAX_VARMINTS,
})

SKILL_POINT_LOCATIONS: dict[str, RACLocationData] = {
    name: RACLocationData(_planet_id(sp.region), sp.region)
    for name, sp in SKILL_POINTS.items()
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
    Rac5Locations.RYLLUS_SPROUT:  RACLocationData(_planet_id(Rac5Planets.RYLLUS), Rac5Planets.RYLLUS),
    Rac5Locations.KALIDON_SHRINK: RACLocationData(_planet_id(Rac5Planets.KALIDON), Rac5Planets.KALIDON),
    # Rac5Locations.METALIS_GLOVES is NOT here — it's an ArmourPickup
    # (ARMOUR_PICKUP_LOCATIONS, see core/armour.py) since it's armour, not a
    # gadget. Defining it in both would create two Location objects with the
    # same name and different ids.
}

SKYBOARD_ITEM_LOCATIONS: dict[str, RACLocationData] = {
    Rac5SkyboardChallenges.KALIDON_LEARNER:          RACLocationData(_planet_id(Rac5Planets.KALIDON), Rac5Planets.KALIDON),
    Rac5SkyboardChallenges.KALIDON_MASTER:           RACLocationData(_planet_id(Rac5Planets.KALIDON), Rac5Planets.KALIDON),
    Rac5SkyboardChallenges.OUTPOST_OMEGA_VERTIGO:    RACLocationData(_planet_id(Rac5Planets.OUTPOST_OMEGA), Rac5Planets.OUTPOST_OMEGA),
    Rac5SkyboardChallenges.OUTPOST_OMEGA_INTERIOR:   RACLocationData(_planet_id(Rac5Planets.OUTPOST_OMEGA), Rac5Planets.OUTPOST_OMEGA),
}

EXTRA_SKYBOARD_LOCATIONS: dict[str, RACLocationData] = {
    Rac5SkyboardChallenges.KALIDON_TICKET:           RACLocationData(_planet_id(Rac5Planets.KALIDON), Rac5Planets.KALIDON),
    Rac5SkyboardChallenges.KALIDON_TRICKY:           RACLocationData(_planet_id(Rac5Planets.KALIDON), Rac5Planets.KALIDON),
    Rac5SkyboardChallenges.OUTPOST_OMEGA_DANGER:     RACLocationData(_planet_id(Rac5Planets.OUTPOST_OMEGA), Rac5Planets.OUTPOST_OMEGA),
    Rac5SkyboardChallenges.OUTPOST_OMEGA_VORTEX:     RACLocationData(_planet_id(Rac5Planets.OUTPOST_OMEGA), Rac5Planets.OUTPOST_OMEGA),
}

# One location per tracked Shrink Ray puzzle-gate bit (see
# core/address_maps's SHRINK_RAY_PUZZLE_BITS) — anchored to Kalidon since
# that's where Shrink Ray first becomes usable; access is gated on owning it
# regardless of which planet the puzzle is actually on (rules/shrink_ray.py).
SHRINK_RAY_SKIP_LOCATIONS: dict[str, RACLocationData] = {
    name: RACLocationData(_planet_id(Rac5Planets.KALIDON), Rac5Planets.KALIDON)
    for name in SHRINK_RAY_SKIP_LOCATION_NAMES
}

CHALLENGE_LOCATIONS: dict[str, RACLocationData] = {
    cp.name: RACLocationData(_planet_id(cp.planet), cp.planet)
    for cp in CHALLENGE_PICKUPS
}

_ALL_CLANK_PICKUPS = DERBY_CLANK_PICKUPS + GADGETBOT_TOSS_CLANK_PICKUPS + GADGETBOT_CLANK_PICKUPS
ALL_CLANK_LOCATIONS: dict[str, RACLocationData] = {
    cp.name: RACLocationData(_planet_id(cp.planet), cp.planet)
    for cp in _ALL_CLANK_PICKUPS
    if cp.name not in CHALLENGE_LOCATIONS  # combined reward-challenge names live in CHALLENGE_LOCATIONS
}

# ClankChallengeGroups default: every group included (matches
# options.py's ClankChallengeGroups.default).
DEFAULT_CLANK_CHALLENGE_GROUPS: dict[str, int] = dict.fromkeys(
    (CHALLENGE_GROUP_DERBY, CHALLENGE_GROUP_GADGETBOT_TOSS, CHALLENGE_GROUP_GADGETBOT), 1
)


def enabled_clank_challenge_names(group_weights: dict[str, int]) -> frozenset[str]:
    """Names of individual Clank Challenge completions (including the
    reward ones in CHALLENGE_LOCATIONS) whose group has a nonzero weight in
    the ClankChallengeGroups option — shared by regions.py (location
    creation) and rules/metalis.py + rules/dayni_moon.py (rule assignment),
    which must agree on the same exclusion.

    Presence in `group_weights`, not `.get(group, 1) > 0` — ItemDict (see
    options.py's ClankChallengeGroups) culls zero-valued entries on its own
    __init__, so a group the player explicitly zeroed out is simply absent
    here, not present with value 0. Defaulting a missing key to "included"
    would silently re-enable exactly the group the player turned off."""
    return frozenset(
        name for name, group in CHALLENGE_NAME_TO_GROUP.items()
        if group in group_weights
    )

# Each entry: (name, region, is_cutscene).
# Enter Planet entries are appended at the end for readability, but IDs are
# freely assigned now (no stability constraint across a renumbering pass).
_MISSION_ENTRIES: list[tuple[str, str, bool]] = [
    (Rac5CutsceneLocations.POKITARU_FIGHT,           Rac5Planets.POKITARU,      False),
    (Rac5CutsceneLocations.RYLLUS_BUZZING,           Rac5Planets.RYLLUS,        True),
    (Rac5CutsceneLocations.RYLLUS_ARTIFACT,          Rac5Planets.RYLLUS,        False),
    (Rac5CutsceneLocations.RYLLUS_TEMPLE,            Rac5Planets.RYLLUS,        False),
    (Rac5CutsceneLocations.KALIDON_EXPLORE,          Rac5Planets.KALIDON,       True),
    (Rac5CutsceneLocations.KALIDON_WIN,              Rac5Planets.KALIDON,       False),
    (Rac5CutsceneLocations.METALIS_WAR,              Rac5Planets.METALIS,       False),
    (Rac5CutsceneLocations.DREAMTIME_COMPLETE,       Rac5Planets.DREAMTIME,     False),
    (Rac5CutsceneLocations.OUTPOST_OMEGA,            Rac5Planets.OUTPOST_OMEGA, True),
    (Rac5CutsceneLocations.OUTPOST_OMEGA_ESCAPE,     Rac5Planets.OUTPOST_OMEGA, False),
    (Rac5CutsceneLocations.OUTPOST_OMEGA_REMATCH,    Rac5Planets.OUTPOST_OMEGA, False),
    # METALIS_CLANK is the shared Giant-Clank-trigger mission bit (see
    # planets.py's GIANT_CLANK_CONFIGS note) — still not tracked/used.
    # (Rac5CutsceneLocations.METALIS_CLANK,          Rac5Planets.CHALLAX,       True),
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
    # Enter Planet
    (Rac5CutsceneLocations.POKITARU_ENTER,           Rac5Planets.POKITARU,      True),
    (Rac5CutsceneLocations.RYLLUS_ENTER,             Rac5Planets.RYLLUS,        True),
    (Rac5CutsceneLocations.KALIDON_ENTER,            Rac5Planets.KALIDON,       True),
    (Rac5CutsceneLocations.METALIS_ENTER,            Rac5Planets.METALIS,       True),
    (Rac5CutsceneLocations.DREAMTIME_ENTER,          Rac5Planets.DREAMTIME,     True),
    (Rac5CutsceneLocations.OUTPOST_OMEGA_ENTER,      Rac5Planets.OUTPOST_OMEGA, True),
    (Rac5CutsceneLocations.CHALLAX_ENTER,            Rac5Planets.CHALLAX,       True),

    (Rac5CutsceneLocations.INSIDE_CLANK_ENTER,       Rac5Planets.INSIDE_CLANK,  True),
    (Rac5CutsceneLocations.QUODRONA_ENTER,           Rac5Planets.QUODRONA,      True),

    (Rac5CutsceneLocations.DREAMTIME_SLEEPING_RATCHET, Rac5Planets.DREAMTIME,   True),
    # Both fired by PlanetInventory.check_giant_clank() (see core/planets.py's
    # GIANT_CLANK_CONFIGS), not the mission-bit table in mission_locations.py.
    (Rac5CutsceneLocations.METALIS_ESCAPE,           Rac5Planets.METALIS,       False),
    (Rac5CutsceneLocations.CHALLAX_CLANK,            Rac5Planets.CHALLAX,       False),
    # Former PRESET_MISSION_BITS — see mission_locations.py's STORY_MISSION_MAP
    # comment and core/core.py's _MISSION_FORCE_RELOAD.
    (Rac5CutsceneLocations.POKITARU_RESCUE,          Rac5Planets.POKITARU,      False),
    (Rac5CutsceneLocations.KALIDON_SEARCH,           Rac5Planets.KALIDON,       False),
    (Rac5CutsceneLocations.CHALLAX_EXPLORE,          Rac5Planets.CHALLAX,       False),
]

_mission_data: dict[str, tuple[RACLocationData, bool]] = {
    name: (RACLocationData(_planet_id(region), region), is_cutscene)
    for name, region, is_cutscene in _MISSION_ENTRIES
}

STORY_MISSION_LOCATIONS: dict[str, RACLocationData] = {
    name: data for name, (data, is_cutscene) in _mission_data.items() if not is_cutscene
}

CUTSCENE_LOCATIONS: dict[str, RACLocationData] = {
    name: data for name, (data, is_cutscene) in _mission_data.items() if is_cutscene
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
    **WEAPON_TITAN_VENDOR_LOCATIONS,
    **WEAPON_LEVEL_LOCATIONS,
    **NANOTECH_LEVEL_LOCATIONS,
    **ARMOUR_SET_CHECK_LOCATIONS,
    **CHALLENGE_LOCATIONS,
    **ALL_CLANK_LOCATIONS,
    **SKYBOARD_ITEM_LOCATIONS,
    **EXTRA_SKYBOARD_LOCATIONS,
    **SHRINK_RAY_SKIP_LOCATIONS,
}

LOCATION_ID_TO_NAME: dict[int, str] = {data.code: name for name, data in ALL_LOCATIONS.items()}


def for_planet(planet: str, *sources: dict[str, RACLocationData]) -> dict[str, RACLocationData]:
    """Subset of one or more location dicts whose region is `planet`. Used by the
    per-planet modules (locations/<planet>.py) to slice the shared registry above
    without redefining or retyping any location."""
    return {
        name: data
        for source in sources
        for name, data in source.items()
        if data.region == planet
    }

# Vendor location ↔ internal-name lookup tables
# Derived here so both the game-state layer and the client can share one source.

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
    Rac5VendorLocations.POKITARU_RYNO:       WEAPON_DISPLAY_TO_INTERNAL["RYNO"],
}

# Titan variant purchase location -> internal weapon name (Challenge Mode 1+,
# every weapon except RYNO — see WEAPON_TITAN_VENDOR_LOCATIONS above).
VENDOR_TITAN_LOC: dict[str, str] = {
    Rac5TitanVendorLocations.POKITARU_LACERATOR_TITAN:   WEAPON_DISPLAY_TO_INTERNAL["Lacerator"],
    Rac5TitanVendorLocations.POKITARU_ACID_TITAN:         WEAPON_DISPLAY_TO_INTERNAL["Acid Bomb Glove"],
    Rac5TitanVendorLocations.POKITARU_CONCUSSION_TITAN:   WEAPON_DISPLAY_TO_INTERNAL["Concussion Gun"],
    Rac5TitanVendorLocations.RYLLUS_AGENTS_TITAN:         WEAPON_DISPLAY_TO_INTERNAL["Agents of Doom"],
    Rac5TitanVendorLocations.KALIDON_SCORCHER_TITAN:      WEAPON_DISPLAY_TO_INTERNAL["Scorcher"],
    Rac5TitanVendorLocations.DREAMTIME_SUCK_TITAN:        WEAPON_DISPLAY_TO_INTERNAL["Suck Cannon"],
    Rac5TitanVendorLocations.OUTPOST_OMEGA_BEE_TITAN:     WEAPON_DISPLAY_TO_INTERNAL["Bee Mine Glove"],
    Rac5TitanVendorLocations.CHALLAX_SNIPER_TITAN:        WEAPON_DISPLAY_TO_INTERNAL["Sniper Mine"],
    Rac5TitanVendorLocations.DAYNI_MOON_MOOTATOR_TITAN:   WEAPON_DISPLAY_TO_INTERNAL["Mootator"],
    Rac5TitanVendorLocations.DAYNI_MOON_SHOCK_TITAN:      WEAPON_DISPLAY_TO_INTERNAL["Shock Rocket"],
    Rac5TitanVendorLocations.INSIDE_CLANK_STATIC_TITAN:   WEAPON_DISPLAY_TO_INTERNAL["Static Barrier"],
    Rac5TitanVendorLocations.QUODRONA_LASER_TITAN:        WEAPON_DISPLAY_TO_INTERNAL["Laser Tracer"],
}

TITAN_INTERNAL_TO_LOCATION: dict[str, str] = {v: k for k, v in VENDOR_TITAN_LOC.items()}

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

    # Challenge Mode 1+ only — confirmed in-game.
    ("agents_of_doom",  1, Rac5ModVendorLocations.KALIDON_AGENTS_EXPLOSIVE),
    ("scorcher",        1, Rac5ModVendorLocations.KALIDON_SCORCHER_SUNFLARE),
    ("suck_cannon",     1, Rac5ModVendorLocations.KALIDON_SUCK_CANNON_BOUNCE),
    ("bee_mine_glove",  2, Rac5ModVendorLocations.KALIDON_BEE_HIVE_BOMB),
    ("sniper_mine",     2, Rac5ModVendorLocations.CHALLAX_SNIPER_SMART_REFLECTOR),
    ("shock_rocket",    2, Rac5ModVendorLocations.CHALLAX_SHOCK_MULTI_LAUNCHER),
    ("static_barrier",  1, Rac5ModVendorLocations.KALIDON_STATIC_REFLECTION),
    ("static_barrier",  2, Rac5ModVendorLocations.QUODRONA_STATIC_MIRAGE),
    ("laser_tracer",    1, Rac5ModVendorLocations.CHALLAX_LASER_PIERCE),
    ("laser_tracer",    2, Rac5ModVendorLocations.QUODRONA_LASER_RICOCHET),
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

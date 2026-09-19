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


MENU_REGION = "Menu"


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

WEAPON_LEVEL_LOOKUP: dict[tuple[str, int], str] = {
    (internal, level): WEAPON_LEVEL_NAMES[internal][level]
    for internal, data in _WEAPON_DATA.items()
    for level in range(2, data.max_level + 1)
}

WEAPON_LEVEL_LOCATIONS: dict[str, RACLocationData] = {
    loc_name: RACLocationData(_shared_id(), Rac5Planets.POKITARU)
    for loc_name in WEAPON_LEVEL_LOOKUP.values()
}

WEAPON_MAX_LEVEL_LOCATIONS: dict[str, RACLocationData] = {
    loc_name: WEAPON_LEVEL_LOCATIONS[loc_name]
    for (_internal, level), loc_name in WEAPON_LEVEL_LOOKUP.items()
    if level == 4
}

WEAPON_SUB_MAX_LEVEL_LOCATIONS: dict[str, RACLocationData] = {
    loc_name: WEAPON_LEVEL_LOCATIONS[loc_name]
    for (_internal, level), loc_name in WEAPON_LEVEL_LOOKUP.items()
    if level in (2, 3)
}

NANOTECH_LEVEL_LOOKUP: dict[int, str] = {
    level: getattr(Rac5NanotechLevels, f"LEVEL_{level}")
    for level in range(6, 76)
}

NANOTECH_LEVEL_LOCATIONS: dict[str, RACLocationData] = {
    loc_name: RACLocationData(_shared_id(), MENU_REGION)
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

NG_PLUS_WEAPON_LEVEL_LOCATIONS: frozenset[str] = frozenset(
    loc_name for (internal, _level), loc_name in WEAPON_LEVEL_LOOKUP.items()
    if internal == Rac5WeaponKeys.RYNO
)

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

# Same Challenge Mode tiers as CHALLENGE_MODE_1_ARMOUR_LOCATIONS/
# CHALLENGE_MODE_2_ARMOUR_LOCATIONS below, but for the "Equip X Armor Set"
# combo checks (core/locations/armour_set_locations.py's ARMOUR_SET_CHECKS)
# that require Hyperborean/Chameleon pieces -- ICE_II needs 3 Hyperborean
# pieces, STALKER needs 2 Chameleon pieces, same as the pure sets.
CHALLENGE_MODE_1_ARMOUR_SET_LOCATIONS: frozenset[str] = frozenset({
    Rac5ArmourSet.HYPERBOREAN,
    Rac5ArmourSet.ICE_II,
})

CHALLENGE_MODE_2_ARMOUR_SET_LOCATIONS: frozenset[str] = frozenset({
    Rac5ArmourSet.CHAMELEON,
    Rac5ArmourSet.STALKER,
})

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
    if cp.name not in CHALLENGE_LOCATIONS
}

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
    # planets.py's GIANT_CLANK_CONFIGS note) — still not tracked/used.
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
    (Rac5CutsceneLocations.METALIS_ESCAPE,           Rac5Planets.METALIS,       False),
    (Rac5CutsceneLocations.CHALLAX_CLANK,            Rac5Planets.CHALLAX,       False),
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

MOD_INTERNAL_TO_LOCATION: dict[tuple[str, str], str] = {
    (w, _ATTR_NAMES[i - 1]): loc for w, i, loc in _MOD_SLOT_ASSIGNMENT
}

MOD_INTERNAL_TO_VENDOR_SLOT_LOCATION: dict[tuple[str, str], str] = {
    (w, ("one", "two", "three")[i - 1]): loc for w, i, loc in _MOD_SLOT_ASSIGNMENT
}


def disabled_weapon_location_names(enabled_weapons: frozenset[str]) -> frozenset[str]:
    """AP location names that belong to a weapon the EnabledWeapons option (see
    options.py) has excluded: that weapon's own vendor/collectible location, its
    Titan variant purchase, every one of its mod-slot purchases, and every one of
    its weapon-level checks. Shared by regions.py (location creation) and every
    rules/<planet>.py file (rule assignment) — both must agree on the same
    exclusion, or set_rule() would target a Location that was never created."""
    disabled_internal = frozenset(
        WEAPON_DISPLAY_TO_INTERNAL[display] for display in WEAPON_DISPLAY_TO_INTERNAL
        if display not in enabled_weapons
    )
    if not disabled_internal:
        return frozenset()
    names: set[str] = set()
    names.update(
        loc for internal, loc in WEAPON_INTERNAL_TO_LOCATION.items() if internal in disabled_internal
    )
    names.update(
        loc for internal, loc in TITAN_INTERNAL_TO_LOCATION.items() if internal in disabled_internal
    )
    names.update(
        loc for (weapon, _slot), loc in MOD_INTERNAL_TO_LOCATION.items() if weapon in disabled_internal
    )
    names.update(
        loc for (internal, _level), loc in WEAPON_LEVEL_LOOKUP.items() if internal in disabled_internal
    )
    return frozenset(names)

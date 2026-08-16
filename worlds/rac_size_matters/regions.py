from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Region

from .constants import Rac5CutsceneLocations, Rac5Planets
from .locations import (
    ALL_CLANK_LOCATIONS,
    ARMOUR_PICKUP_LOCATIONS,
    ARMOUR_SET_CHECK_LOCATIONS,
    BOSS_LOCATIONS,
    CHALLENGE_LOCATIONS,
    CHALLENGE_MODE_1_ARMOUR_LOCATIONS,
    CHALLENGE_MODE_2_ARMOUR_LOCATIONS,
    CHALLENGE_MODE_MAX_LEVEL_LOCATIONS,
    CHALLENGE_MODE_MOD_LOCATIONS,
    CHALLENGE_MODE_RYNO_LOCATION,
    CHALLENGE_MODE_SUB_MAX_LEVEL_LOCATIONS,
    CLANK_CHALLENGE_SKILL_POINT_LOCATIONS,
    CUTSCENE_LOCATIONS,
    EASY_SKILL_POINT_LOCATIONS,
    EXTRA_SKYBOARD_LOCATIONS,
    GADGET_PICKUP_LOCATIONS,
    GADGET_VENDOR_LOCATIONS,
    GIANT_CLANK_LOCATIONS,
    HARD_SKILL_POINT_LOCATIONS,
    NANOTECH_LEVEL_LOCATIONS,
    NG_PLUS_ARMOUR_SET_LOCATIONS,
    NG_PLUS_WEAPON_LEVEL_LOCATIONS,
    SHRINK_RAY_SKIP_LOCATIONS,
    SKYBOARD_CHALLENGE_SKILL_POINT_LOCATIONS,
    SKYBOARD_ITEM_LOCATIONS,
    STORY_MISSION_LOCATIONS,
    TITANIUM_BOLT_LOCATIONS,
    WEAPON_MAX_LEVEL_LOCATIONS,
    WEAPON_MOD_VENDOR_LOCATIONS,
    WEAPON_SUB_MAX_LEVEL_LOCATIONS,
    WEAPON_TITAN_VENDOR_LOCATIONS,
    WEAPON_VENDOR_LOCATIONS,
)

if TYPE_CHECKING:
    from .world import RACSizeMatterWorld

PLANET_NAMES: tuple[str, ...] = (
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


def create_regions(world: RACSizeMatterWorld) -> None:
    from .world import RACLocation

    player = world.player
    multiworld = world.multiworld

    menu_region = Region("Menu", player, multiworld)
    planet_regions: dict[str, Region] = {
        name: Region(name, player, multiworld)
        for name in PLANET_NAMES
    }

    giant_clank = bool(world.options.giant_clank)
    # NG+ Items only controls which NG+-exclusive ITEMS are in the pool
    # (see world.py) — it doesn't gate location existence. Challenge Mode
    # alone gates the tables below; computed once up top rather than
    # per-table like clank_challenges etc.
    ng_plus = bool(world.options.ng_plus_items)
    challenge_mode = world.options.challenge_mode.value

    armour_pickup_locations = ARMOUR_PICKUP_LOCATIONS
    excluded_armour = set(GIANT_CLANK_LOCATIONS) if not giant_clank else set()
    if challenge_mode < 1:
        excluded_armour |= CHALLENGE_MODE_1_ARMOUR_LOCATIONS
    if challenge_mode < 2:
        excluded_armour |= CHALLENGE_MODE_2_ARMOUR_LOCATIONS
    if excluded_armour:
        armour_pickup_locations = {
            name: data for name, data in ARMOUR_PICKUP_LOCATIONS.items()
            if name not in excluded_armour
        }

    weapon_vendor_locations = WEAPON_VENDOR_LOCATIONS
    if challenge_mode < 1:
        weapon_vendor_locations = {
            name: data for name, data in WEAPON_VENDOR_LOCATIONS.items()
            if name not in CHALLENGE_MODE_RYNO_LOCATION
        }

    location_tables = [
        TITANIUM_BOLT_LOCATIONS,
        armour_pickup_locations,
        BOSS_LOCATIONS,
        GADGET_PICKUP_LOCATIONS,
        weapon_vendor_locations,
        GADGET_VENDOR_LOCATIONS,
    ]
    if challenge_mode >= 1:
        location_tables.append(WEAPON_TITAN_VENDOR_LOCATIONS)
    if world.options.all_missions:
        story_missions = STORY_MISSION_LOCATIONS
        if world.options.clank_challenges.value < 1:
            # METALIS_WAR triggers on completing the Buzzsaw Blitz clank
            # challenge, which never unlocks with clank challenges off —
            # drop it rather than create an unreachable location.
            story_missions = {
                name: data for name, data in story_missions.items()
                if name != Rac5CutsceneLocations.METALIS_WAR
            }
        if not giant_clank:
            story_missions = {
                name: data for name, data in story_missions.items()
                if name not in GIANT_CLANK_LOCATIONS
            }
        location_tables.append(story_missions)
    if world.options.all_cutscenes:
        location_tables.append(CUTSCENE_LOCATIONS)
    if world.options.skill_points.value >= 1:
        easy_skill_points = EASY_SKILL_POINT_LOCATIONS
        if not giant_clank:
            easy_skill_points = {
                name: data for name, data in easy_skill_points.items()
                if name not in GIANT_CLANK_LOCATIONS
            }
        location_tables.append(easy_skill_points)
    if world.options.skill_points.value >= 2:
        hard_skill_points = HARD_SKILL_POINT_LOCATIONS
        if not giant_clank:
            hard_skill_points = {
                name: data for name, data in hard_skill_points.items()
                if name not in GIANT_CLANK_LOCATIONS
            }
        location_tables.append(hard_skill_points)
    if world.options.enable_clank_challenge_skill_points:
        location_tables.append(CLANK_CHALLENGE_SKILL_POINT_LOCATIONS)
    if world.options.enable_skyboard_challenge_skill_points:
        location_tables.append(SKYBOARD_CHALLENGE_SKILL_POINT_LOCATIONS)
    weapon_mod_vendor_locations = WEAPON_MOD_VENDOR_LOCATIONS
    if challenge_mode < 1:
        weapon_mod_vendor_locations = {
            name: data for name, data in WEAPON_MOD_VENDOR_LOCATIONS.items()
            if name not in CHALLENGE_MODE_MOD_LOCATIONS
        }
    location_tables.append(weapon_mod_vendor_locations)
    if world.options.clank_challenges.value >= 1:
        location_tables.append(CHALLENGE_LOCATIONS)
    if world.options.clank_challenges.value >= 2:
        location_tables.append(ALL_CLANK_LOCATIONS)
    if world.options.skyboard_challenges.value >= 1:
        location_tables.append(SKYBOARD_ITEM_LOCATIONS)
        location_tables.append(EXTRA_SKYBOARD_LOCATIONS)
    if world.options.shrink_ray_locations:
        location_tables.append(SHRINK_RAY_SKIP_LOCATIONS)
    if world.options.armour_set_checks:
        armour_set_locations = ARMOUR_SET_CHECK_LOCATIONS
        if not ng_plus:
            armour_set_locations = {
                name: data for name, data in ARMOUR_SET_CHECK_LOCATIONS.items()
                if name not in NG_PLUS_ARMOUR_SET_LOCATIONS
            }
        location_tables.append(armour_set_locations)
    if world.options.weapon_level_checks.value >= 1:
        max_level_locations = WEAPON_MAX_LEVEL_LOCATIONS
        if not ng_plus:
            max_level_locations = {
                name: data for name, data in WEAPON_MAX_LEVEL_LOCATIONS.items()
                if name not in NG_PLUS_WEAPON_LEVEL_LOCATIONS
            }
        location_tables.append(max_level_locations)
        if challenge_mode >= 1:
            location_tables.append(CHALLENGE_MODE_MAX_LEVEL_LOCATIONS)
    if world.options.weapon_level_checks.value >= 2:
        sub_max_level_locations = WEAPON_SUB_MAX_LEVEL_LOCATIONS
        if not ng_plus:
            sub_max_level_locations = {
                name: data for name, data in WEAPON_SUB_MAX_LEVEL_LOCATIONS.items()
                if name not in NG_PLUS_WEAPON_LEVEL_LOCATIONS
            }
        location_tables.append(sub_max_level_locations)
        if challenge_mode >= 1:
            location_tables.append(CHALLENGE_MODE_SUB_MAX_LEVEL_LOCATIONS)
    if world.options.nanotech_level_checks:
        location_tables.append(NANOTECH_LEVEL_LOCATIONS)

    for table in location_tables:
        for loc_name, loc_data in table.items():
            region = planet_regions[loc_data.region]
            location = RACLocation(player, loc_name, loc_data.code, region)
            region.locations.append(location)

    quodrona = planet_regions[Rac5Planets.QUODRONA]
    victory_loc = RACLocation(player, "Quodrona Completed", None, quodrona)
    victory_loc.place_locked_item(world.create_event("Victory"))
    quodrona.locations.append(victory_loc)

    for planet in PLANET_NAMES:
        menu_region.connect(planet_regions[planet], f"To {planet}")

    multiworld.regions += [menu_region, *planet_regions.values()]

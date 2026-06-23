from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Region

from .constants import RACSMPLANET
from .locations import (
    ALL_CLANK_LOCATIONS,
    ARMOUR_PICKUP_LOCATIONS,
    ARMOUR_SET_CHECK_LOCATIONS,
    BOSS_LOCATIONS,
    CHALLENGE_LOCATIONS,
    CLANK_CHALLENGE_SKILL_POINT_LOCATIONS,
    CUTSCENE_LOCATIONS,
    EASY_SKILL_POINT_LOCATIONS,
    EXTRA_SKYBOARD_LOCATIONS,
    GADGET_PICKUP_LOCATIONS,
    GADGET_VENDOR_LOCATIONS,
    HARD_SKILL_POINT_LOCATIONS,
    SKYBOARD_CHALLENGE_SKILL_POINT_LOCATIONS,
    SKYBOARD_ITEM_LOCATIONS,
    STORY_MISSION_LOCATIONS,
    TITANIUM_BOLT_LOCATIONS,
    WEAPON_MOD_VENDOR_LOCATIONS,
    WEAPON_VENDOR_LOCATIONS,
)

if TYPE_CHECKING:
    from .world import RACSizeMatterWorld

PLANET_NAMES: tuple[str, ...] = (
    RACSMPLANET.POKITARU,
    RACSMPLANET.RYLLUS,
    RACSMPLANET.KALIDON,
    RACSMPLANET.METALIS,
    RACSMPLANET.DREAMTIME,
    RACSMPLANET.OUTPOST_OMEGA,
    RACSMPLANET.CHALLAX,
    RACSMPLANET.DAYNI_MOON,
    RACSMPLANET.INSIDE_CLANK,
    RACSMPLANET.QUODRONA,
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

    location_tables = [
        TITANIUM_BOLT_LOCATIONS,
        ARMOUR_PICKUP_LOCATIONS,
        BOSS_LOCATIONS,
        GADGET_PICKUP_LOCATIONS,
        WEAPON_VENDOR_LOCATIONS,
        GADGET_VENDOR_LOCATIONS,
    ]
    if world.options.all_missions:
        location_tables.append(STORY_MISSION_LOCATIONS)
    if world.options.all_cutscenes:
        location_tables.append(CUTSCENE_LOCATIONS)
    if world.options.skill_points.value >= 1:
        location_tables.append(EASY_SKILL_POINT_LOCATIONS)
    if world.options.skill_points.value >= 2:
        location_tables.append(HARD_SKILL_POINT_LOCATIONS)
    if world.options.enable_clank_challenge_skill_points:
        location_tables.append(CLANK_CHALLENGE_SKILL_POINT_LOCATIONS)
    if world.options.enable_skyboard_challenge_skill_points:
        location_tables.append(SKYBOARD_CHALLENGE_SKILL_POINT_LOCATIONS)
    location_tables.append(WEAPON_MOD_VENDOR_LOCATIONS)
    if world.options.clank_challenges.value >= 1:
        location_tables.append(CHALLENGE_LOCATIONS)
    if world.options.clank_challenges.value >= 2:
        location_tables.append(ALL_CLANK_LOCATIONS)
    if world.options.skyboard_challenges.value >= 1:
        location_tables.append(SKYBOARD_ITEM_LOCATIONS)
        location_tables.append(EXTRA_SKYBOARD_LOCATIONS)
    if world.options.armour_set_checks:
        location_tables.append(ARMOUR_SET_CHECK_LOCATIONS)

    for table in location_tables:
        for loc_name, loc_data in table.items():
            region = planet_regions[loc_data.region]
            location = RACLocation(player, loc_name, loc_data.code, region)
            region.locations.append(location)

    quodrona = planet_regions[RACSMPLANET.QUODRONA]
    victory_loc = RACLocation(player, "Quodrona Completed", None, quodrona)
    victory_loc.place_locked_item(world.create_event("Victory"))
    quodrona.locations.append(victory_loc)

    for planet in PLANET_NAMES:
        menu_region.connect(planet_regions[planet], f"To {planet}")

    multiworld.regions += [menu_region, *planet_regions.values()]

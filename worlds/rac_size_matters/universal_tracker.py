"""Universal Tracker integration for Ratchet & Clank: Size Matters"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from worlds.rac_size_matters.world import RACSizeMatterWorld

PLANET_TO_MAP_INDEX: dict[str, int] = {
    "Pokitaru":     1,
    "Ryllus":       2,
    "Kalidon":      3,
    "Metalis":      4,
    "Dreamtime":    5,
    "Outpost Omega": 6,
    "Challax":      7,
    "Dayni Moon":   8,
    "Inside Clank": 9,
    "Quodrona":     10,
}

PLANET_ID_TO_REGION: dict[int, str] = {
    0x01: "Pokitaru",
    0x02: "Ryllus",
    0x03: "Kalidon",
    0x04: "Metalis",
    0x05: "Dreamtime",
    0x06: "Outpost Omega",
    0x07: "Challax",
    0x08: "Dayni Moon",
    0x09: "Inside Clank",
    0x0A: "Quodrona",
    0x17: "Outpost Omega",
}


def setup_options_from_slot_data(world: "RACSizeMatterWorld") -> None:
    """Set options from passthrough slot data when re-generating for Universal Tracker."""
    if hasattr(world.multiworld, "re_gen_passthrough"):
        if world.game in world.multiworld.re_gen_passthrough:
            world.using_ut = True
            world.passthrough = world.multiworld.re_gen_passthrough[world.game]
            world.options.all_missions.value = world.passthrough.get("all_missions", True)
            world.options.all_cutscenes.value = world.passthrough.get("all_cutscenes", False)
            world.options.progressive_weapons.value = world.passthrough["progressive_weapons"]
            world.options.progressive_mods.value = world.passthrough.get("progressive_mods", False)
            world.options.progressive_armour.value = world.passthrough["progressive_armour"]
            world.options.death_link.value = world.passthrough["death_link"]
            world.options.clank_challenges.value = world.passthrough.get("clank_challenges", 0)
            world.options.skyboard_challenges.value = world.passthrough.get("skyboard_challenges", 0)
            world.options.skill_points.value = world.passthrough.get("skill_points", True)
            world.options.enable_clank_challenge_skill_points.value = \
                world.passthrough.get("enable_clank_challenge_skill_points", False)
            world.options.enable_skyboard_challenge_skill_points.value = \
                world.passthrough.get("enable_skyboard_challenge_skill_points", False)

            world.options.armour_set_checks.value = world.passthrough["armour_set_checks"]
            world.options.starting_weapons.value = world.passthrough["starting_weapons"]
            world.options.starting_gadgets.value = world.passthrough["starting_gadgets"]
            world.options.starting_bolts.value = world.passthrough["starting_bolts"]
            world.options.death_amnesty.value = world.passthrough["death_amnesty"]
        else:
            world.using_ut = False
    else:
        world.using_ut = False


def map_page_index(data: str) -> int:
    """Return the maps.json index for the given planet name. Defaults to Galaxy (0)."""
    return PLANET_TO_MAP_INDEX.get(data, 0)


tracker_world: dict[str, Any] = {
    "map_page_maps": "tracker/maps.json",
    "map_page_locations": "tracker/locations.json",
    "map_page_setting_key": r"rsm_current_planet_{player}_{team}",
    "map_page_index": map_page_index,
}

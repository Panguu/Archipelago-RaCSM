"""Universal Tracker integration: tracker map data and slot-data passthrough regen."""
import json
import unittest
from pathlib import Path

from test.general import setup_solo_multiworld

from ..locations import ALL_LOCATIONS
from ..universal_tracker import PLANET_ID_TO_REGION, PLANET_TO_MAP_INDEX, setup_options_from_slot_data
from ..world import RACSizeMatterWorld
from .bases import RACSizeMatterTestBase

WORLD_DIR = Path(__file__).resolve().parent.parent

# Slot data keys the client consumes but which have no effect on tracker logic.
NOT_PASSED_THROUGH = {
    "split_infobots",
    "starting_planet_id",
    "ammo_link",
    "bolt_link",
    "ghost_link",
    "ghost_link_update_interval",
    "starting_skin",
    "trap_duration",
}


def _walk_sections(nodes: list[dict]):
    for node in nodes:
        yield node
        yield from _walk_sections(node.get("children", []))


class TestTrackerData(unittest.TestCase):
    def setUp(self) -> None:
        self.maps = json.loads((WORLD_DIR / "tracker/maps.json").read_text(encoding="utf-8"))
        self.nodes = list(_walk_sections(
            json.loads((WORLD_DIR / "tracker/locations.json").read_text(encoding="utf-8"))
        ))

    def test_map_images_exist(self) -> None:
        for page in self.maps:
            self.assertTrue((WORLD_DIR / page["img"]).is_file(), page["img"])

    def test_map_pins_reference_known_maps(self) -> None:
        map_names = {page["name"] for page in self.maps}
        for node in self.nodes:
            for pin in node.get("map_locations", []):
                self.assertIn(pin["map"], map_names, node["name"])

    def test_section_icons_exist(self) -> None:
        for node in self.nodes:
            for section in node.get("sections", []):
                if "icon" in section:
                    self.assertTrue((WORLD_DIR / "tracker" / section["icon"]).is_file(), section["icon"])

    def test_sections_match_location_table(self) -> None:
        sections = {s["name"] for node in self.nodes for s in node.get("sections", [])}
        self.assertEqual(sections - set(ALL_LOCATIONS), set(), "tracker names not in the location table")
        self.assertEqual(set(ALL_LOCATIONS) - sections, set(), "locations missing from the tracker")

    def test_map_page_index_matches_maps_json(self) -> None:
        for planet, index in PLANET_TO_MAP_INDEX.items():
            self.assertEqual(self.maps[index]["name"], planet)
        for region in PLANET_ID_TO_REGION.values():
            self.assertIn(region, PLANET_TO_MAP_INDEX)


class TestSlotDataPassthrough(RACSizeMatterTestBase):
    run_default_tests = False
    options = {
        "all_cutscenes": True,
        "giant_clank": True,
        "starting_weapons": 1,
        "starting_gadgets": 2,
        "starting_bolts": 50_000,
        "nanotech_level_max": 50,
        "bolt_multiplier": 2,
    }

    def test_regen_from_slot_data_restores_options(self) -> None:
        slot_data = self.world.fill_slot_data()

        regen = setup_solo_multiworld(RACSizeMatterWorld, ())
        regen.re_gen_passthrough = {RACSizeMatterWorld.game: slot_data}
        world = regen.worlds[1]
        setup_options_from_slot_data(world)

        self.assertTrue(world.using_ut)
        regen_slot_data = world.fill_slot_data()
        for key, value in slot_data.items():
            if key in NOT_PASSED_THROUGH:
                continue
            self.assertEqual(regen_slot_data[key], value, f"slot data key {key!r} not restored by passthrough")

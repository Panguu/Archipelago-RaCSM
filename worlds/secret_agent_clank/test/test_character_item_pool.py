import unittest

from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from test.general import setup_multiworld

from ..constants import ALL_CASES, CASE_NAME_TO_INFOBOT
from ..core.inventories import resolve_owned_cases
from ..items import CASE_GADGET_ITEM_TABLE, INFOBOT_ITEM_TABLE, RATCHET_PACK_ITEM_TABLE, RATCHET_WEAPON_ITEM_TABLE
from ..world import SecretAgentClankWorld


class CharacterItemPoolTests(unittest.TestCase):
    def test_qwark_only_fills_with_an_accessible_native_start(self):
        for mode in ("cases", "progressive_planet"):
            for progressive in ("off", "automatic"):
                with self.subTest(mode=mode, progressive=progressive):
                    world = setup_multiworld(SecretAgentClankWorld, seed=12345, options={
                        "operatives": {"Qwark": 1}, "goal": "qwark_opera",
                        "all_missions": "level_completion", "infobots": mode,
                        "progressive_weapons": progressive})
                    names = [i.name for i in world.itempool]
                    starting = [i.name for i in world.precollected_items[1]]
                    disabled_items = (set(RATCHET_WEAPON_ITEM_TABLE)
                                      | set(RATCHET_PACK_ITEM_TABLE))
                    self.assertFalse(disabled_items.intersection(names + starting))
                    self.assertTrue(set(CASE_GADGET_ITEM_TABLE).intersection(names + starting))
                    regions = {r.name for r in world.get_regions(1)}
                    expected_cases = {item for case, item in CASE_NAME_TO_INFOBOT.items() if case in regions}
                    if mode == "cases":
                        self.assertEqual(set(names + starting) & set(INFOBOT_ITEM_TABLE), expected_cases)
                    sac = world.worlds[1]
                    self.assertIn(sac.starting_case,
                                  resolve_owned_cases(starting, planet_cases=sac.planet_cases))
                    self.assertTrue(CollectionState(world).can_reach(sac.starting_case, "Region", 1))
                    if mode == "progressive_planet":
                        active = {case.name for case in ALL_CASES if case.name in regions}
                        self.assertEqual({name for cases in sac.planet_cases.values() for name in cases}, active)
                        self.assertEqual(sac.fill_slot_data()["planet_cases"], sac.planet_cases)
                    self.assertEqual(len(world.itempool), len(world.get_unfilled_locations(1)))
                    distribute_items_restrictive(world)
                    self.assertTrue(world.fulfills_accessibility())

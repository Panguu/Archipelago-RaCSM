import unittest

from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from test.general import setup_multiworld

from ..constants import CASE_NAME_TO_INFOBOT, SACCases
from ..core.inventories.case_unlocks import resolve_owned_cases
from ..items import GADGET_ITEM_TABLE, INFOBOT_ITEM_TABLE, RATCHET_PACK_ITEM_TABLE, WEAPON_ITEM_TABLE
from ..world import SecretAgentClankWorld


class CharacterItemPoolTests(unittest.TestCase):
    def test_qwark_only_fills_with_an_accessible_native_start(self):
        for mode in ("cases", "planets", "progressive_planet", "character_unlocks"):
            for progressive in (False, True):
                with self.subTest(mode=mode, progressive=progressive):
                    world = setup_multiworld(SecretAgentClankWorld, seed=12345, options={
                        "operatives": {"Qwark": 1}, "goal": "qwark_opera",
                        "all_missions": "level_completion", "infobots": mode,
                        "progressive_weapons": progressive})
                    names = [i.name for i in world.itempool]
                    starting = [i.name for i in world.precollected_items[1]]
                    disabled_items = set(WEAPON_ITEM_TABLE) | set(GADGET_ITEM_TABLE) | set(RATCHET_PACK_ITEM_TABLE)
                    self.assertFalse(disabled_items.intersection(names + starting))
                    self.assertNotIn(CASE_NAME_TO_INFOBOT[SACCases.BOLTAIRE_MUSEUM], names + starting)
                    regions = {r.name for r in world.get_regions(1)}
                    expected_cases = {item for case, item in CASE_NAME_TO_INFOBOT.items() if case in regions}
                    if mode == "cases":
                        self.assertEqual(set(names + starting) & set(INFOBOT_ITEM_TABLE), expected_cases)
                    sac = world.worlds[1]
                    self.assertIn(sac.starting_case,
                                  resolve_owned_cases(starting, character_unlocks=mode == "character_unlocks",
                                                      progressive_planets=sac.progressive_planets))
                    self.assertTrue(CollectionState(world).can_reach(sac.starting_case, "Region", 1))
                    if mode == "progressive_planet":
                        self.assertLessEqual(len(sac.progressive_planets), 5)
                        self.assertEqual(sac.fill_slot_data()["progressive_planets"], sac.progressive_planets)
                    self.assertEqual(len(world.itempool), len(world.get_unfilled_locations(1)))
                    distribute_items_restrictive(world)
                    self.assertTrue(world.fulfills_accessibility())

import unittest

from BaseClasses import CollectionState
from test.general import setup_multiworld

from ..constants import Rac5Gadgets, Rac5Locations, Rac5TBolts
from ..items import CLANK_PACK_NAME
from ..locations import ALL_LOCATIONS
from ..options import Logic
from ..universal_tracker import setup_options_from_slot_data
from ..world import RACSizeMatterWorld


class TestLogic(unittest.TestCase):
    def test_routes_and_tracker_round_trip(self):
        for tier in (Logic.option_easy, Logic.option_normal, Logic.option_glitched):
            with self.subTest(tier=tier):
                mw = setup_multiworld(RACSizeMatterWorld, seed=123, options={
                    "logic": tier, "clank_pack": True, "starting_weapons": 0,
                    "starting_gadgets": 0,
                })
                world = mw.worlds[1]

                def reachable(name, *items):
                    state = CollectionState(mw)
                    for item in items:
                        state.collect(world.create_item(item), prevent_sweep=True)
                    return ALL_LOCATIONS[name].rule.resolve(world)(state)

                shrink = Rac5Gadgets.SHRINK_RAY
                hyper = Rac5Gadgets.HYPERSHOT
                pack = CLANK_PACK_NAME
                # All nine Quodrona routes retain both gadgets at every tier.
                quodrona = [name for name in ALL_LOCATIONS if name.startswith("Quodrona:")
                            and "HasClankPack" in str(ALL_LOCATIONS[name].rule)]
                self.assertEqual(len(quodrona), 9)
                for name in quodrona:
                    self.assertEqual(reachable(name, shrink, hyper), tier >= Logic.option_normal, name)
                    self.assertTrue(reachable(name, shrink, hyper, pack), name)
                    self.assertFalse(reachable(name, hyper, pack), name)
                    self.assertFalse(reachable(name, shrink, pack), name)

                name = Rac5TBolts.KALIDON_RAMP
                self.assertEqual(reachable(name, shrink, hyper), tier >= Logic.option_normal)
                self.assertTrue(reachable(name, shrink, hyper, pack))
                self.assertFalse(reachable(name, hyper, pack))
                self.assertFalse(reachable(name, shrink, pack))
                self.assertEqual(reachable(Rac5TBolts.KALIDON_FACTORY), tier == Logic.option_glitched)
                self.assertTrue(reachable(Rac5TBolts.KALIDON_FACTORY, hyper))
                self.assertEqual(reachable(Rac5Locations.KALIDON_BOOTS, shrink), tier == Logic.option_glitched)
                self.assertFalse(reachable(Rac5Locations.KALIDON_BOOTS, hyper))
                self.assertTrue(reachable(Rac5Locations.KALIDON_BOOTS, shrink, hyper))
                self.assertEqual(reachable(Rac5TBolts.POKITARU_ZIPLINE, pack), tier == Logic.option_glitched)
                self.assertFalse(reachable(Rac5TBolts.POKITARU_ZIPLINE))
                self.assertTrue(reachable(Rac5TBolts.POKITARU_ZIPLINE, pack, "Lacerator"))

                slot_data = world.fill_slot_data()
                self.assertEqual(slot_data["logic"], tier)
                mw.re_gen_passthrough = {world.game: slot_data}
                world.options.logic.value = 99
                setup_options_from_slot_data(world)
                self.assertEqual(world.options.logic.value, tier)
                del slot_data["logic"]
                setup_options_from_slot_data(world)
                self.assertEqual(world.options.logic.value, Logic.option_easy)

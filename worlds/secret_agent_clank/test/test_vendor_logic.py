import json
import random
import unittest

from BaseClasses import CollectionState
from rule_builder.rules import Has
from test.general import setup_multiworld

from ..constants import SACClankGadgets, VENDOR_CASES
from ..vendor_logic import VendorLogic, export_vendor_rules
from ..world import SecretAgentClankWorld
from ..client.vendor_scouts import VendorScouts
from ..core.patches import VendorCatalog
from ..core import Core
from .test_runtime import TEST_BUILD, Memory


class VendorLogicTests(unittest.TestCase):
    def test_exported_rules_match_reachability_across_inventory_changes(self):
        for mode in ("cases", "progressive_planet"):
            for progressive in range(3):
                with self.subTest(mode=mode, progressive=progressive):
                    mw = setup_multiworld(SecretAgentClankWorld, seed=12345, options={
                        'infobots': mode, 'progressive_weapons': progressive,
                        'all_missions': 1, 'all_cutscenes': True,
                        'ng_plus': 1, 'progressive_challenge_mode': True})
                    world = mw.worlds[1]
                    data = json.loads(json.dumps(world.fill_slot_data()['vendor_rules']))
                    logic = VendorLogic(data)
                    locations = [loc for loc in mw.get_locations(1) if loc.name in VENDOR_CASES]
                    state = CollectionState(mw)
                    received = [item.name for item in mw.precollected_items[1]]
                    items = list(mw.itempool)
                    random.Random(42).shuffle(items)

                    def check():
                        self.assertEqual(logic.available(received),
                                         {loc.name for loc in locations if loc.can_reach(state)})

                    check()
                    for item in items:
                        state.collect(item)
                        received.append(item.name)
                        check()
                    for item in reversed(items):
                        state.remove(item)
                        received.remove(item.name)
                        check()

    def test_changed_location_rule_is_used_without_a_client_gate_change(self):
        mw = setup_multiworld(SecretAgentClankWorld, seed=12345)
        world = mw.worlds[1]
        loc = next(loc for loc in mw.get_locations(1) if loc.name in VENDOR_CASES)
        world.set_rule(loc, Has(SACClankGadgets.JETBOOTS))
        logic = VendorLogic(json.loads(json.dumps(export_vendor_rules(world))))
        names = [item.name for item in mw.itempool] + [item.name for item in mw.precollected_items[1]]
        names = [name for name in names if name != SACClankGadgets.JETBOOTS]
        self.assertNotIn(loc.name, logic.available(names))
        self.assertIn(loc.name, logic.available(names + [SACClankGadgets.JETBOOTS]))
        core = Core(Memory(), permanent_build=TEST_BUILD)
        core.vendor_logic = logic
        core.apply_inventory(ratchet={}, clank={}, received_names=names)
        self.assertNotIn(loc.name, core.native_runtime.available_vendor_locations)
        core.apply_inventory(ratchet={}, clank={}, received_names=names + [SACClankGadgets.JETBOOTS])
        self.assertIn(loc.name, core.native_runtime.available_vendor_locations)

    def test_location_filter_and_scouts_preserve_individual_offers(self):
        p = Memory()
        catalog = VendorCatalog(p)
        catalog.location_descriptors = [(0x120007, 'base', 1), (0x12000F, 'titan', 3)]
        p.batch_write_int8([(0x130000, 2)])  # Already purchased transaction flag.
        for available, expected in ((set(), (255, 255)), ({'base'}, (1, 255)),
                                    ({'titan'}, (255, 3)), ({'base', 'titan'}, (1, 3))):
            catalog.sync_locations(available)
            self.assertEqual(tuple(p.batch_read_int8([0x120007, 0x12000F])), expected)
            self.assertEqual(p.read_int8(0x130000), 2)
            scouts = VendorScouts({'base': 1, 'titan': 2})
            self.assertEqual(scouts.request({1, 2}, vendor_locations=available)['locations'],
                             sorted({'base': 1, 'titan': 2}[name] for name in available))

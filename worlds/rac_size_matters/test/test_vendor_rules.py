import json
import random
from collections import Counter
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

from BaseClasses import CollectionState
from NetUtils import decode, encode

from ..constants import Rac5VendorLocations, Rac5TitanVendorLocations
from ..core.vendor import VendorInventory
from ..client.vendor import InventoryMixin
from ..locations import MENU_REGION
from ..vendor_rules import build_vendor_rules, location_accessible
from .bases import RACSizeMatterTestBase


class TestVendorRuleParity(RACSizeMatterTestBase):
    options = {"starting_weapons": 0, "starting_gadgets": 0}

    def test_export_matches_reachability(self):
        payload = json.loads(json.dumps(self.world.fill_slot_data()["vendor_rules"]))
        rng = random.Random(1234)
        pool = self.multiworld.itempool + self.multiworld.precollected_items[self.player]
        for chance in (0, 0.2, 0.5, 0.8, 1):
            for _ in range(10):
                state = CollectionState(self.multiworld)
                for item in pool:
                    if rng.random() < chance:
                        state.collect(item, prevent_sweep=True)
                for name in payload["locations"]:
                    location = self.multiworld.get_location(name, self.player)
                    self.assertEqual(location_accessible(payload, name, state.prog_items[self.player]),
                                     location.can_reach(state), name)

    def test_dreamtime_needs_only_outpost(self):
        rules = build_vendor_rules(self.world)
        self.assertFalse(location_accessible(rules, Rac5VendorLocations.DREAMTIME_SUCK, {}))
        self.assertTrue(location_accessible(rules, Rac5VendorLocations.DREAMTIME_SUCK, {"Infobot: Outpost Omega": 1}))

    def test_connected_packet_within_json_depth_limit(self):
        # decode() applies the same depth limit CommonClient enforces on server packets.
        decode(encode([{"cmd": "Connected", "slot_data": self.world.fill_slot_data()}]))


class TestProgressiveVendorRuleParity(TestVendorRuleParity):
    options = {**TestVendorRuleParity.options, "challenge_mode": 2,
               "progressive_challenge_mode": 1, "progressive_weapons": 1, "clank_pack": 1,
               "all_cutscenes": 1, "clank_challenges": 2, "skyboard_challenges": 1,
               "skill_points": 2, "weapon_level_checks": 4}


class TestFixedChallengeVendorRuleParity(TestVendorRuleParity):
    options = {**TestVendorRuleParity.options, "challenge_mode": 2}


class TestVendorRuleMenu(TestCase):
    def setUp(self):
        self.weapons = SimpleNamespace(vendor_locations={}, titan_purchased={}, gadgets={},
                                       get_level=lambda name: 3)
        self.vendor = VendorInventory(None, SimpleNamespace(weapons=self.weapons),
                                      SimpleNamespace(is_vendor_accessible=lambda name: name == "DREAMTIME"), Mock())
        self.base = Rac5VendorLocations.DREAMTIME_SUCK
        self.titan = Rac5TitanVendorLocations.DREAMTIME_SUCK_TITAN

    def test_rules_override_legacy_and_preserve_purchase_transition(self):
        self.vendor.configure_rules({"version": 2, "regions": {}, "locations": {
            self.base: [MENU_REGION, ["has", "Infobot: Outpost Omega", 1]],
            self.titan: [MENU_REGION, ["has", "Progressive Challenge Mode", 1]],
        }})
        self.assertNotIn("suck_cannon", self.vendor._purchasable_names())
        self.vendor.rule_items = Counter({"Infobot: Outpost Omega": 1})
        self.assertEqual(self.vendor.purchasable_locations(), [self.base])
        self.weapons.vendor_locations[self.base] = True
        self.assertEqual(self.vendor.purchasable_locations(), [])
        self.vendor.rule_items["Progressive Challenge Mode"] = 1
        self.assertEqual(self.vendor.purchasable_locations(), [self.titan])
        self.weapons.titan_purchased["suck_cannon"] = True
        self.assertEqual(self.vendor.purchasable_locations(), [])

    def test_old_seed_fallback_and_reconnect_reset(self):
        self.vendor.configure_rules({"version": 2, "regions": {}, "locations": {}})
        self.assertEqual(self.vendor._purchasable_names(), [])
        self.vendor.configure_rules(None)
        self.assertIn("suck_cannon", self.vendor._purchasable_names())
        self.assertEqual(self.vendor.rule_items, {})

    def test_unknown_version_is_rejected(self):
        with self.assertRaises(ValueError):
            self.vendor.configure_rules({"version": 1, "locations": {}})

    def test_mod_rule_and_item_sync(self):
        self.vendor.configure_rules({"version": 2, "regions": {"Gated": [[MENU_REGION, ["true"]]]}, "locations": {
            "mod": ["Gated", ["has", "Progressive Challenge Mode", 2]],
        }})
        context = InventoryMixin()
        context._wiring = SimpleNamespace(vendor=self.vendor)
        context.game = "test"
        context.item_names = {"test": {1: "Progressive Challenge Mode"}}
        context.items_received = [SimpleNamespace(item=1)]
        self.vendor.force_refresh = Mock()
        context._sync_vendor_rule_items()
        self.assertFalse(self.vendor._is_mod_location_accessible("mod"))
        context.items_received.append(SimpleNamespace(item=1))
        context._sync_vendor_rule_items()
        self.assertTrue(self.vendor._is_mod_location_accessible("mod"))
        self.assertFalse(self.vendor._is_mod_location_accessible("absent"))
        self.assertEqual(self.vendor.force_refresh.call_count, 2)
        context._sync_vendor_rule_items()
        self.assertEqual(self.vendor.force_refresh.call_count, 2)

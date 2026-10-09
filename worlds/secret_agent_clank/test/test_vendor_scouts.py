import unittest
from types import SimpleNamespace

from ..client.vendor_scouts import VendorScouts
from ..constants.planets import SACCases
from ..locations import BASE_VENDOR_LOCATIONS, LOCATION_NAME_TO_ID, MOD_VENDOR_LOCATIONS, TITAN_VENDOR_LOCATIONS


class VendorScoutTests(unittest.TestCase):
    def setUp(self):
        self.scouts = VendorScouts({})
        self.scouts.locations = {(0, 5): 100, (3, 19): 101, (4, 5): 102}

    def test_only_enabled_locations_scouted_without_hints(self):
        self.assertEqual(self.scouts.request({100, 102, 999}, owned_cases={SACCases.GALACTIC_BOLT_RESERVE}), {
            "cmd": "LocationScouts", "locations": [100, 102], "create_as_hint": 0})

    def test_scouts_unlock_only_the_matching_case(self):
        self.assertEqual(self.scouts.request({100, 101, 102})["locations"], [])
        self.assertEqual(self.scouts.request({100, 101, 102}, hint=True,
            owned_cases={SACCases.THE_SHOWERS}), {
                "cmd": "LocationScouts", "locations": [101], "create_as_hint": 2})
        self.assertEqual(self.scouts.request({100, 101, 102}, owned_cases={
            SACCases.THE_SHOWERS, SACCases.GALACTIC_BOLT_RESERVE})["locations"], [100, 101, 102])

    def test_native_offer_resolves_recipient_game_item_without_price_changes(self):
        item = SimpleNamespace(location=100, item=900, player=2, flags=1)
        called = []
        def item_name(item_id, slot):
            called.append((item_id, slot))
            return "Progressive Sword"
        self.scouts.update([item], item_name, lambda slot: "Other Player")
        row = SimpleNamespace(node_type=0, weapon_id=5, mod_id=0, price=35000)
        result = self.scouts.for_row(row)
        self.assertEqual(called, [(900, 2)])
        self.assertEqual(result.description, "Progressive Sword\nFor Other Player")
        self.assertEqual(result.title_color, "orange")
        self.assertTrue(result.progression)
        self.assertEqual(row.price, 35000)
        self.assertIsNone(self.scouts.for_row(SimpleNamespace(node_type=2, weapon_id=5, mod_id=0)))

    def test_mod_and_titan_locations_are_distinct_and_unscouted_is_unknown(self):
        self.assertIsNone(self.scouts.for_row(SimpleNamespace(node_type=4, weapon_id=5, mod_id=0)))
        items = [SimpleNamespace(location=n, item=n+1000, player=1, flags=0)
                 for n in (100, 101, 102, 999)]
        self.scouts.update(items, lambda i,p: str(i), lambda p: "Pangu")
        for kind,key,location in ((0,5,100),(3,19,101),(4,5,102)):
            row=SimpleNamespace(node_type=kind, weapon_id=key, mod_id=key)
            self.assertEqual(self.scouts.for_row(row).location_id,location)
            self.assertEqual(self.scouts.for_row(row).title_color, "white")
        self.assertNotIn(999,self.scouts.rewards)

    def test_every_generated_vendor_location_has_a_native_scout_row(self):
        definitions = {**BASE_VENDOR_LOCATIONS, **MOD_VENDOR_LOCATIONS, **TITAN_VENDOR_LOCATIONS}
        ids = {name: LOCATION_NAME_TO_ID[name] for name in definitions}
        scouts = VendorScouts(ids)
        self.assertEqual(set(scouts.locations.values()), set(ids.values()))
        self.assertTrue(all(": Agency Vendor: " in name for name in definitions))

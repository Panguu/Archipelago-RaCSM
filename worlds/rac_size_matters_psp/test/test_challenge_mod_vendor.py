import unittest
from unittest.mock import Mock

from .test_client_gameplay import GameMemory
from ..core.core import Core
from ..core.vendor import (_CHALLENGE_MODE_MOD_LOCATIONS,
                           _MOD_LOCATION_TO_PLANET_KEY, _SLOT_TO_UNLOCK_ATTR)
from ..locations import MOD_INTERNAL_TO_LOCATION
from ..constants import Rac5GadgetKeys


class TestChallengeModVendor(unittest.TestCase):
    def setUp(self):
        self.core = Core(GameMemory())
        self.core.clank_enabled = False
        self.core.tick()
        self.vendor = self.core.vendor
        self.weapons = self.vendor.weapons
        self.vendor.controller = lambda: None
        self.vendor.send_location = Mock()
        self.core.planet_unlock.is_vendor_accessible = lambda key: True
        for gadget in (Rac5GadgetKeys.SHRINK_RAY, Rac5GadgetKeys.POLARIZER):
            self.weapons.gadgets[gadget] = True

    def test_all_generated_mods_have_runtime_routes(self):
        self.assertEqual(set(MOD_INTERNAL_TO_LOCATION.values()),
                         set(_MOD_LOCATION_TO_PLANET_KEY))
        self.assertEqual(len(_CHALLENGE_MODE_MOD_LOCATIONS), 10)

    def test_tiers_gate_hints_and_native_purchase_flags(self):
        for tier in (0, 1, 2, 0):
            self.vendor.challenge_mode = tier
            self.vendor._apply_mod_unlock_flags()
            hints = set(self.vendor.mod_locations())
            for (weapon, slot), location in MOD_INTERNAL_TO_LOCATION.items():
                expected = tier > 0 or location not in _CHALLENGE_MODE_MOD_LOCATIONS
                with self.subTest(tier=tier, location=location):
                    self.assertEqual(location in hints, expected)
                    self.assertEqual(self.weapons.get_mod_unlock(
                        weapon, _SLOT_TO_UNLOCK_ATTR[slot]), expected)

    def test_challenge_tier_does_not_bypass_planet_or_gadget_requirements(self):
        self.vendor.challenge_mode = 2
        self.core.planet_unlock.is_vendor_accessible = lambda key: key == 'CHALLAX'
        for gadget in (Rac5GadgetKeys.SHRINK_RAY, Rac5GadgetKeys.POLARIZER):
            self.weapons.gadgets[gadget] = False
            self.assertEqual(self.vendor.mod_locations(), [])
            self.weapons.gadgets[gadget] = True
        self.assertEqual(set(self.vendor.mod_locations()), {
            loc for loc, planet in _MOD_LOCATION_TO_PLANET_KEY.items() if planet == 'CHALLAX'})

    def test_challenge_purchase_reports_once_and_display_grants_are_removed(self):
        self.vendor.challenge_mode = 1
        self.vendor.mod_vendor()
        self.vendor.send_location.assert_not_called()
        pairs = [(pair, loc) for pair, loc in MOD_INTERNAL_TO_LOCATION.items()
                 if loc in _CHALLENGE_MODE_MOD_LOCATIONS]
        for (weapon, slot), location in pairs:
            self.weapons.set_mod(weapon, slot, True)
        self.vendor.mod_vendor()
        self.vendor.mod_vendor()
        self.assertCountEqual([call.args[0] for call in self.vendor.send_location.call_args_list],
                              [loc for pair, loc in pairs])
        self.assertFalse(any(self.weapons.weapons.values()))
        self.vendor.close()
        for (weapon, slot), location in pairs:
            self.assertFalse(self.weapons.get(weapon))
            self.assertFalse(self.weapons.get_mod(weapon, slot))
            self.assertTrue(self.weapons.vendor_locations[location])

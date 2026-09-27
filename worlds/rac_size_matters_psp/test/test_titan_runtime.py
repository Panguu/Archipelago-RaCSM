import unittest
from unittest.mock import Mock
from types import SimpleNamespace

from .test_client_gameplay import GameMemory
from ..core.core import Core
from ..core.controller import PauseSelectButtons
from ..core.address_maps import WEAPON_VENDOR_ITEMS, WEAPON_VENDOR_SLOTS
from ..core.vendor import MAX_VENDOR_SLOTS
from ..core.weapons import WEAPON_MAX_LEVELS, PROGRESSIVE_MANUAL, PROGRESSIVE_AUTOMATIC
from ..locations import TITAN_INTERNAL_TO_LOCATION, WEAPON_INTERNAL_TO_LOCATION


class TestTitanRuntime(unittest.TestCase):
    def test_native_first_open_list_overwrite_is_repaired_without_false_purchase(self):
        self.vendor.weapon_vendor()
        memory = self.vendor.pine
        expected = memory.read_bytes(WEAPON_VENDOR_ITEMS, MAX_VENDOR_SLOTS * 4 + 4)
        # Simulate native initialization replacing the AP list after entry.
        memory.write_bytes(WEAPON_VENDOR_ITEMS, bytes(MAX_VENDOR_SLOTS * 4))
        memory.write_int32(WEAPON_VENDOR_SLOTS, 0)
        self.vendor.weapon_vendor()
        self.assertEqual(memory.read_bytes(WEAPON_VENDOR_ITEMS, len(expected)), expected)
        self.vendor.send_location.assert_not_called()
        memory.write_bytes = Mock(wraps=memory.write_bytes)
        self.core.planet.menu.set = Mock()
        self.vendor.weapon_vendor()
        memory.write_bytes.assert_not_called()
        self.core.planet.menu.set.assert_not_called()
        # A real purchase is still processed before list repair.
        memory.write_int32(WEAPON_VENDOR_SLOTS, 0)
        self.weapons.set('lacerator', True)
        self.vendor.weapon_vendor()
        self.vendor.send_location.assert_called_once_with(WEAPON_INTERNAL_TO_LOCATION['lacerator'])

    def test_ammo_list_drift_does_not_switch_back_to_purchase_view(self):
        self.vendor._is_weapon_ap_owned = lambda name: name == 'lacerator'
        self.weapons.weapons['lacerator'] = True
        self.weapons.set('lacerator', True)
        self.vendor.weapon_vendor()
        self.press(PauseSelectButtons.D_PAD_RIGHT)
        memory = self.vendor.pine
        expected = memory.read_bytes(WEAPON_VENDOR_ITEMS, MAX_VENDOR_SLOTS * 4 + 4)
        memory.write_int32(WEAPON_VENDOR_SLOTS, 0)
        self.vendor.weapon_vendor()
        self.assertFalse(self.vendor.show_purchasable_weapons)
        self.assertEqual(memory.read_bytes(WEAPON_VENDOR_ITEMS, len(expected)), expected)
        self.vendor.send_location.assert_not_called()

    def setUp(self):
        self.core = Core(GameMemory())
        self.core.clank_enabled = False
        self.core.tick()
        self.vendor = self.core.vendor
        self.weapons = self.vendor.weapons
        self.vendor.controller = lambda: None
        self.vendor.send_location = Mock()
        self.core.planet_unlock.is_vendor_accessible = lambda key: True
        self.vendor.challenge_mode = self.weapons.challenge_mode = 1

    def press(self, button):
        self.vendor.controller = lambda: SimpleNamespace(pressed=lambda key: key == button)
        self.vendor.weapon_vendor()
        self.vendor.controller = lambda: None

    def test_base_then_titan_are_distinct_checks_without_level_or_ownership_grants(self):
        weapon = 'lacerator'
        base = WEAPON_INTERNAL_TO_LOCATION[weapon]
        titan = TITAN_INTERNAL_TO_LOCATION[weapon]
        self.weapons.set_level(weapon, 2)
        self.weapons.set_experience(weapon, 456)
        self.vendor._is_weapon_level_checks_enabled = lambda: True
        self.vendor.weapon_vendor()
        self.vendor.send_location.assert_not_called()
        self.assertEqual(self.vendor.purchase_location(weapon), base)
        self.weapons.set(weapon, True)
        self.vendor.weapon_vendor()
        self.assertEqual(self.vendor.purchase_location(weapon), titan)
        self.assertEqual(self.weapons.get_level(weapon), 4)
        self.assertIn(titan, self.vendor.purchasable_locations())
        self.assertFalse(self.weapons.get(weapon))
        self.weapons.set(weapon, True)
        self.weapons.set_experience(weapon, 0)
        self.vendor.weapon_vendor()
        self.vendor.weapon_vendor()
        self.assertEqual([c.args[0] for c in self.vendor.send_location.call_args_list], [base, titan])
        self.assertTrue(self.weapons.titan_purchased[weapon])
        self.assertNotIn(weapon, self.vendor._purchasable_names())
        self.vendor.close()
        self.assertFalse(self.weapons.weapons[weapon])
        self.assertEqual(self.weapons.get_level(weapon), 2)
        self.assertEqual(self.weapons.get_experience(weapon), 456)

    def test_ammo_view_restores_real_progress_and_does_not_buy_titan(self):
        weapon = 'lacerator'
        self.vendor._is_weapon_ap_owned = lambda name: name == weapon
        self.weapons.weapons[weapon] = True
        self.weapons.set(weapon, True)
        self.weapons.set_level(weapon, 3)
        self.weapons.set_experience(weapon, 789)
        self.weapons.vendor_locations[WEAPON_INTERNAL_TO_LOCATION[weapon]] = True
        self.vendor.weapon_vendor()
        self.assertEqual(self.weapons.get_level(weapon), 4)
        self.press(PauseSelectButtons.D_PAD_RIGHT)
        self.assertEqual(self.weapons.get_level(weapon), 3)
        self.assertTrue(self.weapons.get(weapon))
        self.press(PauseSelectButtons.D_PAD_LEFT)
        self.assertEqual(self.weapons.get_level(weapon), 4)
        self.assertFalse(self.weapons.get(weapon))
        self.vendor.send_location.assert_not_called()
        self.vendor.close()
        self.assertEqual(self.weapons.get_level(weapon), 3)
        self.assertEqual(self.weapons.get_experience(weapon), 789)

    def test_titan_replay_is_idempotent_and_does_not_grant_weapon(self):
        locations = set(TITAN_INTERNAL_TO_LOCATION.values())
        self.weapons.sync_from_ap(locations)
        self.weapons.sync_from_ap(locations)
        self.assertTrue(all(self.weapons.titan_purchased.values()))
        self.assertFalse(any(self.weapons.weapons.values()))
        self.assertFalse(self.vendor._is_titan_eligible('ryno'))

    def test_mootator_requires_real_level_four_and_dayni_access(self):
        self.weapons.set_level('mootator', 2)
        self.assertNotIn('mootator', self.vendor._purchasable_names())
        self.weapons.set_level('mootator', 3)
        self.assertIn('mootator', self.vendor._purchasable_names())
        self.vendor.weapon_vendor()
        self.assertEqual(self.weapons.get_level('mootator'), 4)
        self.assertIn('mootator', self.vendor._purchasable_names())
        self.core.planet_unlock.is_vendor_accessible = lambda key: key != 'DAYNI_MOON'
        self.assertNotIn('mootator', self.vendor._purchasable_names())

    def test_tier_zero_and_ryno_have_no_titan_offers(self):
        self.vendor.challenge_mode = 0
        for name, location in WEAPON_INTERNAL_TO_LOCATION.items():
            self.weapons.vendor_locations[location] = True
            self.assertFalse(self.vendor._is_titan_pending(name))
        self.assertTrue(set(TITAN_INTERNAL_TO_LOCATION.values()).isdisjoint(self.vendor.purchasable_locations()))
        self.assertEqual(WEAPON_MAX_LEVELS['ryno'], 4)
        self.assertEqual(WEAPON_MAX_LEVELS['lacerator'], 8)

    def test_vanilla_titan_ceiling_is_removed_without_granting_levels(self):
        self.weapons.set_level('lacerator', 6)
        self.weapons.apply_progressive_leveling()
        self.assertEqual(self.weapons.get_level('lacerator'), 3)
        self.weapons.titan_purchased['lacerator'] = True
        self.weapons.apply_progressive_leveling()
        self.assertEqual(self.weapons.get_level('lacerator'), 3)
        self.weapons.set_level('lacerator', 6)
        self.weapons.apply_progressive_leveling()
        self.assertEqual(self.weapons.get_level('lacerator'), 6)

    def test_progressive_modes_match_ps2_titan_boundary(self):
        self.weapons.progressive_mode = PROGRESSIVE_MANUAL
        self.weapons.level_caps['lacerator'] = 5
        self.weapons.set_level('lacerator', 2)
        self.weapons.apply_progressive_leveling()
        self.assertEqual(self.weapons.get_level('lacerator'), 2)
        self.weapons.set_level('lacerator', 3)
        self.weapons.apply_progressive_leveling()
        self.assertEqual(self.weapons.get_level('lacerator'), 4)
        self.weapons.progressive_mode = PROGRESSIVE_AUTOMATIC
        self.weapons.level_caps['lacerator'] = 7
        self.weapons.apply_progressive_leveling()
        self.assertEqual(self.weapons.get_level('lacerator'), 7)

    def test_titan_xp_boost_and_level_reports_stop_at_maximum(self):
        self.weapons.set('lacerator', True)
        self.weapons.set_level('lacerator', 5)
        self.weapons.set_experience('lacerator', 100)
        self.weapons.experience_multiplier = 2
        self.weapons._prev_experience['lacerator'] = 90
        self.weapons.apply_experience_boost()
        self.assertEqual(self.weapons.get_experience('lacerator'), 110)
        self.weapons._raw_level['lacerator'] = 5
        self.weapons.set_level('lacerator', 9999999)
        levels = self.weapons.check()['levels']
        self.assertEqual(levels, [('lacerator', 7), ('lacerator', 8)])

    def test_every_titan_offer_routes_to_its_own_check(self):
        self.assertEqual(len(TITAN_INTERNAL_TO_LOCATION), 12)
        for name, titan in TITAN_INTERNAL_TO_LOCATION.items():
            with self.subTest(weapon=name):
                base = WEAPON_INTERNAL_TO_LOCATION.get(name)
                if base:
                    self.weapons.vendor_locations[base] = True
                else:
                    self.weapons.set_level(name, 3)
                self.assertEqual(self.vendor.purchase_location(name), titan)
                self.assertIn(titan, self.vendor.purchasable_locations())

    def test_vendor_display_progress_is_never_persisted(self):
        from ..client.psp_mixin import PspMixin
        snapshot = Mock(side_effect=AssertionError('display levels must not be saved'))
        ctx = SimpleNamespace(slot=1, psp_connected=True, _server_state_ready=True,
            _weapon_state_restored=True, _wiring=SimpleNamespace(vendor_active=True,
                planet=SimpleNamespace(is_ready=True,
                    weapons=SimpleNamespace(level_experience_snapshot=snapshot))))
        PspMixin._maybe_persist_weapon_state(ctx)
        snapshot.assert_not_called()

    def test_reward_text_uses_titan_scout_instead_of_base_scout(self):
        from ..client.context import RACContext
        from ..core.vendor import WEAPON_VENDOR_IDS
        weapon = 'lacerator'
        base = WEAPON_INTERNAL_TO_LOCATION[weapon]
        titan = TITAN_INTERNAL_TO_LOCATION[weapon]
        self.weapons.vendor_locations[base] = True
        ctx = SimpleNamespace(_wiring=self.core,
            _location_name_to_id={base:1, titan:2},
            locations_info={1:SimpleNamespace(item=10, player=1),
                            2:SimpleNamespace(item=20, player=2)},
            item_names=SimpleNamespace(lookup_in_slot=lambda item, player: str(item)),
            player_names={1:'Base recipient',2:'Titan recipient'})
        self.assertEqual(RACContext._vendor_reward_for_id(ctx, WEAPON_VENDOR_IDS[weapon]),
                         ('20', 'Titan recipient'))

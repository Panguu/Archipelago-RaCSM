import unittest

from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from test.general import setup_multiworld

from ..constants.challenge_mode import CHALLENGE_VENDOR_LOCATIONS, PROGRESSIVE_CHALLENGE_MODE
from ..constants.nanotech import nanotech_location_name
from ..constants.weapon_progression import level_location_name
from ..core.patches.progression import Progression
from ..core.patches.vendor_catalog import VendorCatalog
from ..options import BoltMultiplier, HealthXPMultiplier, NgPlus, WeaponXPMultiplier
from ..universal_tracker import setup_options_from_slot_data
from ..world import SecretAgentClankWorld
from .test_runtime import Memory


class ChallengeModeTests(unittest.TestCase):
    def test_defaults_and_slider_label(self):
        self.assertEqual(NgPlus.display_name, "Max Challenge Mode")
        for option in (WeaponXPMultiplier, HealthXPMultiplier, BoltMultiplier):
            self.assertEqual(option.default, 5)
        world = setup_multiworld(SecretAgentClankWorld).worlds[1]
        slot = world.fill_slot_data()
        for key in ("weapon_xp_multiplier", "health_xp_multiplier", "bolt_multiplier"):
            self.assertEqual(slot[key], 5)
        self.assertFalse(slot["progressive_challenge_mode"])

    def test_pool_counts_and_fill_for_each_maximum(self):
        for progressive in (False, True):
            for maximum in range(3):
                with self.subTest(progressive=progressive, maximum=maximum):
                    mw = setup_multiworld(SecretAgentClankWorld, seed=12345, options={
                        "progressive_challenge_mode": progressive, "ng_plus": maximum})
                    self.assertEqual(sum(i.name == PROGRESSIVE_CHALLENGE_MODE for i in mw.itempool),
                                     maximum if progressive else 0)
                    self.assertEqual(len(mw.itempool), len(mw.get_unfilled_locations(1)))
                    slot = mw.worlds[1].fill_slot_data()
                    self.assertEqual(slot["ng_plus"], maximum)
                    self.assertEqual(slot["progressive_challenge_mode"], progressive)
                    distribute_items_restrictive(mw)
                    self.assertTrue(mw.fulfills_accessibility())

    def test_received_history_caps_and_replays_without_incrementing_twice(self):
        p = Progression(Memory())
        for maximum in range(3):
            p.configure({"ng_plus": maximum, "progressive_challenge_mode": True,
                         "progressive_weapons": "2"})
            for count in (0, 1, 2, 5, 2, 0):
                history = [PROGRESSIVE_CHALLENGE_MODE] * count + ["Progressive Dual Lacerators (Ratchet)"] * 8
                p.receive(history)
                self.assertEqual(p.ng_plus, min(count, maximum))
                self.assertEqual(p.levels["blaster"], 8 if min(count, maximum) else 4)
                p.receive(history)
                self.assertEqual(p.ng_plus, min(count, maximum))

    def test_legacy_and_disabled_use_fixed_level(self):
        for maximum in range(3):
            p = Progression(Memory())
            p.configure({"ng_plus": maximum})
            p.receive([PROGRESSIVE_CHALLENGE_MODE] * 5)
            self.assertEqual(p.ng_plus, maximum)

    def test_receipts_update_native_challenge_level(self):
        mem = Memory()
        p = Progression(mem)
        p.configure({"ng_plus": 2, "progressive_challenge_mode": True})
        p.base, p.ng_address = 0x100000, 0x300ED4
        for count in (0, 1, 2, 3):
            p.receive([PROGRESSIVE_CHALLENGE_MODE] * count)
            p.sync()
            self.assertEqual(mem.read_int32(p.ng_address), min(count, 2))

    def test_challenge_checks_require_first_unlock(self):
        mw = setup_multiworld(SecretAgentClankWorld, options={
            "ng_plus": 2, "progressive_challenge_mode": True, "weapon_level_checks": "all",
            "nanotech_checks": True})
        state = CollectionState(mw)
        for item in (*mw.itempool, *mw.precollected_items[1]):
            if item.name != PROGRESSIVE_CHALLENGE_MODE:
                state.collect(item, prevent_sweep=True)
        names = [loc.name for loc in mw.get_locations(1) if loc.name in CHALLENGE_VENDOR_LOCATIONS]
        names += [nanotech_location_name(61), level_location_name("blaster", 5)]
        for name in names:
            self.assertFalse(mw.get_location(name, 1).can_reach(state), name)
        self.assertTrue(mw.get_location(nanotech_location_name(60), 1).can_reach(state))
        state.collect(mw.worlds[1].create_item(PROGRESSIVE_CHALLENGE_MODE))
        for name in names:
            self.assertTrue(mw.get_location(name, 1).can_reach(state), name)

    def test_shop_unlock_refreshes_without_case_change_or_flag_reset(self):
        mem = Memory()
        catalog = VendorCatalog(mem)
        catalog.case_descriptors = [(0x100000, "owned", 1), (0x100008, "owned", 3)]
        catalog.challenge_descriptors = {0x100008}
        for level, expected in ((0, 255), (1, 3), (2, 3), (0, 255)):
            catalog.challenge_level = level
            catalog.sync_cases({"owned"})
            self.assertEqual(mem.read_int8(0x100000), 1)
            self.assertEqual(mem.read_int8(0x100008), expected)

    def test_tracker_restores_progression_and_legacy_defaults(self):

        mw = setup_multiworld(SecretAgentClankWorld, options={
            "ng_plus": 2, "progressive_challenge_mode": True})
        world = mw.worlds[1]
        slot = world.fill_slot_data()
        mw.re_gen_passthrough = {world.game: slot}
        world.options.progressive_challenge_mode.value = False
        world.options.ng_plus.value = 0
        setup_options_from_slot_data(world)
        self.assertTrue(world.options.progressive_challenge_mode)
        self.assertEqual(world.options.ng_plus.value, 2)
        del slot["progressive_challenge_mode"]
        setup_options_from_slot_data(world)
        self.assertFalse(world.options.progressive_challenge_mode)

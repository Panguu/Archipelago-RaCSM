import unittest

from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from test.general import setup_multiworld

from ..constants import (
    CHALLENGE_VENDOR_LOCATIONS,
    PROGRESSIVE_CHALLENGE_MODE,
    NativeFunctions,
    SACClankGadgets,
    SACPickups,
    level_location_name,
    nanotech_location_name,
)
from ..core.patches import Progression, VendorCatalog, jump, packed
from ..core.patches.module_arena import ModuleArena
from ..options import BoltMultiplier, HealthXPMultiplier, NgPlus, WeaponXPMultiplier
from ..universal_tracker import setup_options_from_slot_data
from ..world import SecretAgentClankWorld
from .test_runtime import Memory
from .mips_cpu import CPU


class ChallengeModeTests(unittest.TestCase):
    def test_challenge_pickups_use_ap_level_before_save_initialization(self):
        for maximum, progressive, count in ((1, False, 0), (2, False, 0),
                                           (1, True, 0), (1, True, 1),
                                           (2, True, 0), (2, True, 1), (2, True, 2)):
            with self.subTest(maximum=maximum, progressive=progressive, count=count):
                mem = Memory()
                p = Progression(mem)
                p.configure({'ng_plus': maximum, 'progressive_challenge_mode': progressive})
                p.receive([PROGRESSIVE_CHALLENGE_MODE] * count)
                replay, getter, init = 0x110000, 0x120000, 0x140000
                mem.write_bytes(replay + 0x1C, packed([0x3C020021, 0x8C448000,
                                                      0x8C830ED4, 0x0003182B]))
                mem.write_bytes(getter + 0x20, packed([0x8C42005C]))
                mem.write_bytes(init + 0x38, packed([0x9042001C, 0x10400007, 0x8E510058,
                    jump(replay, True), 0, 0x14400004, 0x3C05005F]))
                xp, bolts = 0x170000, 0x170100
                mem.write_bytes(xp, packed([0x27BDFFB0, 0xFFB30028]))
                mem.write_bytes(bolts, packed([0x27BDFFF0, 0xFFB00000]))
                symbols = {'GLOBALVARS_IsInReplayMode__Fv': replay,
                    'GADGET_GetCurrentPowerLevel__FUi': getter,
                    'GADGET_g_GadgetList': 0x100000, 'WeaponPickup_Init__FP4Moby': init,
                    NativeFunctions.GADGET_GETS_XP: xp, NativeFunctions.PLAYER_GRANT_BOLTS: bolts}
                arena = ModuleArena(0x180000, bytes(4096), 128)
                patches = p.prepare(symbols, 31, arena, vendor_enabled=False)
                for patch in patches + arena.patches:
                    mem.write_bytes(patch.address, patch.replacement)
                # The native save pointer is still null, just as at the loader
                # gate. Object initialization must already see the AP setting.
                self.assertEqual(mem.read_int32(p.save_pointer_address), 0)
                mem.batch_write_int8([(0x16001C, 1)])
                cpu = CPU(mem)
                cpu.r[2], cpu.r[18] = 0x160000, 0x150000
                cpu.run(init + 0x38, stop=init + (0x60 if p.ng_plus else 0x54))
                self.assertEqual(cpu.r[2], p.ng_plus)

    def test_progressive_receipt_updates_pickup_gate_for_native_restarts(self):
        mem = Memory()
        p = Progression(mem)
        p.configure({'ng_plus': 2, 'progressive_challenge_mode': True})
        p.base, p.pickup_challenge_address = 0x100000, 0x180000
        for count in (0, 1, 2):
            p.receive([PROGRESSIVE_CHALLENGE_MODE] * count)
            p.sync()
            self.assertEqual(mem.read_int32(p.pickup_challenge_address), count)

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
        names += [nanotech_location_name(61), level_location_name("blaster", 5),
                  SACPickups.BOLTAIRE_MUSEUM_THERM_OPTIC_SHADES]
        for name in names:
            self.assertFalse(mw.get_location(name, 1).can_reach(state), name)
        self.assertTrue(mw.get_location(nanotech_location_name(60), 1).can_reach(state))
        state.collect(mw.worlds[1].create_item(PROGRESSIVE_CHALLENGE_MODE))
        for name in names:
            self.assertTrue(mw.get_location(name, 1).can_reach(state), name)

    def test_therm_optic_shades_pickup_is_challenge_mode_only(self):
        for maximum in range(3):
            with self.subTest(maximum=maximum):
                mw = setup_multiworld(SecretAgentClankWorld, options={"ng_plus": maximum})
                names = {loc.name for loc in mw.get_locations(1)}
                self.assertEqual(SACPickups.BOLTAIRE_MUSEUM_THERM_OPTIC_SHADES in names, maximum > 0)
                pool = {item.name for item in (*mw.itempool, *mw.precollected_items[1])}
                self.assertIn(SACClankGadgets.THERM_OPTIC_SHADES, pool)

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

    def test_tracker_restores_progression(self):

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

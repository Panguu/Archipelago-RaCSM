import unittest
from unittest.mock import Mock

from ..constants.clank_gadgets import SACClankWeapons
from ..constants.planets import SACCases
from ..constants.weapon_mods import WEAPON_MODS
from ..constants.weapons import EQUIPMENT_DISPLAY_TO_INTERNAL, SACRatchetWeapons
from ..core.inventories.weapons import WEAPON_ORDER
from ..core.patches import MARKER, GameFlags, LocationHooks
from .test_location_hooks import run_routine
from .test_runtime import Memory


class VendorCaseUnlockTests(unittest.TestCase):
    def setUp(self):
        self.p = Memory()
        self.hooks = LocationHooks(self.p)
        self.hooks.installed = True
        self.hooks.module = 1
        self.hooks.marker_address = 0x120000
        self.p.data[0x120000:0x120000 + len(MARKER)] = MARKER
        self.p.batch_write_int32([(0x206328, 1)])
        self.slot = WEAPON_ORDER.index(EQUIPMENT_DISPLAY_TO_INTERNAL[SACClankWeapons.HOLOKNUCKLES])
        self.mod = next(m for m in WEAPON_MODS if m.weapon == SACRatchetWeapons.BLASTER)
        self.hooks.tables = {"vendor": 0x130000, "mods": 0x130040, "titan": 0x130080,
                             "pickup": 0x1300C0}
        self.hooks.locations = {"vendor": {self.slot: "base"}, "mods": {self.mod.mod_id: "mod"},
                                "titan": {self.slot: "titan"}, "pickup": {self.slot: "pickup"}}
        self.addresses = [self.hooks.tables[kind] + slot for kind, slot in
                          (("vendor", self.slot), ("mods", self.mod.mod_id), ("titan", self.slot))]
        self.p.batch_write_int8(list(zip(self.addresses, (1, 1, 3))))
        self.p.batch_write_int8([(self.hooks.tables["pickup"] + self.slot, 1)])

    def test_locked_offers_are_hidden_without_reporting_checks(self):
        self.hooks.sync_vendor_cases({SACCases.AZCOTAL_ALLEY})
        self.assertEqual(self.p.batch_read_int8(self.addresses), [4, 4, 4])
        self.assertEqual(self.hooks.poll(), [])
        self.assertEqual(self.p.read_int8(self.hooks.tables["pickup"] + self.slot), 1)
        self.hooks.sync_vendor_cases({SACCases.BOLTAIRE_MUSEUM})
        self.assertEqual(self.p.batch_read_int8(self.addresses), [1, 1, 3])
        self.assertEqual(self.hooks.poll(), [])

    def test_purchases_stay_checked_across_case_changes(self):
        self.hooks.sync_vendor_cases(set())
        self.hooks.sync_checked({"base", "mod", "titan"})
        self.hooks.sync_vendor_cases({SACCases.BOLTAIRE_MUSEUM})
        self.assertEqual(self.p.batch_read_int8(self.addresses), [2, 2, 2])
        self.hooks.sync_vendor_cases(set())
        self.assertEqual(self.p.batch_read_int8(self.addresses), [2, 2, 2])
        self.assertEqual(self.hooks.poll(), [])

    def test_locked_base_flag_returns_nonzero_without_native_ownership(self):
        code = GameFlags._build_routine(0x180000, 0x200000, record=False)
        target, registers, _ = run_routine(code, self.slot, 4)
        self.assertEqual(target, 0x700000)
        self.assertNotEqual(registers[2], 0)

    def test_stale_module_is_not_written(self):
        self.p.batch_write_int32([(0x206328, 2)])
        self.hooks.sync_vendor_cases(set())
        self.assertEqual(self.p.batch_read_int8(self.addresses), [1, 1, 3])

    def test_incoming_offers_are_gated_before_loader_release(self):
        self.p.batch_write_int32([(0x206328, 2)])
        gate = Mock(pine=self.p)
        gate.held_module.return_value = self.hooks.module
        self.hooks.sync_vendor_cases(set(), loader_gate=gate)
        self.assertEqual(self.p.batch_read_int8(self.addresses), [4, 4, 4])
        gate.held_module.return_value = 3
        with self.assertRaises(RuntimeError):
            self.hooks.sync_vendor_cases({SACCases.BOLTAIRE_MUSEUM}, loader_gate=gate)

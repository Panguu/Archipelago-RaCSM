import unittest
from unittest.mock import Mock

from ..constants import PROGRESSIVE_WRENCH, SACRatchetWrenchWeapons
from ..core import Core
from ..core.patches import WrenchProgression
from .test_runtime import TEST_BUILD, Memory


class WrenchTests(unittest.TestCase):
    def setUp(self):
        self.p = Memory()
        self.p.write_int32 = lambda a, n: self.p.batch_write_int32([(a, n)])
        self.w = WrenchProgression(self.p)
        self.w.enabled = True

    def test_progressive_entitlements_use_native_mod_order(self):
        for count in range(6):
            self.w.receive([PROGRESSIVE_WRENCH] * count)
            self.assertEqual(self.w.has_wrench, count > 0)
            self.assertEqual(list(self.w.entitlements().values()), [count >= n + 2 for n in range(4)])

    def test_individual_items_unlock_in_any_order(self):
        self.w.receive([SACRatchetWrenchWeapons.WILDBURSTWRENCHMOD])
        self.assertFalse(self.w.has_wrench)
        self.assertEqual(list(self.w.entitlements().values()), [False, False, False, True])
        self.w.receive([SACRatchetWrenchWeapons.WILDBURSTWRENCHMOD, SACRatchetWrenchWeapons.WRENCH])
        self.assertTrue(self.w.has_wrench)

    def test_selected_power_drops_back_when_its_mod_is_missing(self):
        self.w.module = 3
        self.w.ownership_address = 0x110000
        self.w.power_address = 0x110004
        self.w.receive([SACRatchetWrenchWeapons.WRENCH, SACRatchetWrenchWeapons.TRIPLEWAVEWRENCHMOD])
        self.p.batch_write_int32([(0x206328, 3), (0x206324, 0xFFFFFFFF), (0x110004, 2)])
        self.w.sync()
        self.assertEqual(self.p.read_int32(0x110004), 2)
        self.p.batch_write_int32([(0x110004, 1)])
        self.w.sync()
        self.assertEqual(self.p.read_int32(0x110004), 0)

    def test_non_ratchet_modules_get_no_code_changes(self):
        for module in (1, 2, 4, 10, 11, 31):
            symbols = Mock()
            self.assertEqual(self.w.prepare(symbols, module, Mock()), [])
            symbols.get.assert_not_called()

    def test_first_copy_changes_only_ownership_data(self):
        self.w.module = 3
        self.w.ownership_address = 0x110000
        self.w.power_address = 0x110004
        self.p.batch_write_int32([(0x206328, 3), (0x206324, 0xFFFFFFFF), (0x100000, 0x30A20020)])
        self.w.sync()
        self.assertEqual(self.p.read_int32(0x110000), 0)
        self.w.receive([PROGRESSIVE_WRENCH])
        self.w.sync()
        self.assertEqual(self.p.read_int32(0x100000), 0x30A20020)
        self.assertEqual(self.p.read_int32(0x110000), 1)

    def test_unbound_ownership_never_falls_back_to_instruction_writes(self):
        self.w.module = 3
        self.p.batch_write_int32([(0x206328, 3), (0x206324, 0xFFFFFFFF)])
        self.p.writes.clear()
        self.w.sync()
        self.assertEqual(self.p.writes, [])

    def test_received_copies_override_individual_mods(self):
        c = Core(self.p, permanent_build=TEST_BUILD)
        c.wrench.enabled = True
        c.apply_inventory(ratchet={}, clank={}, received_names=["Progressive Wrench"] * 3)
        e = c._entitlements()
        self.assertEqual([e[n] for n in range(28, 32)], [True, True, False, False])

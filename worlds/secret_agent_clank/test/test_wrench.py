import unittest
from unittest.mock import Mock

from ..core.core import Core
from ..core.patches.wrench import WrenchProgression
from .test_runtime import Memory


class WrenchTests(unittest.TestCase):
    def setUp(self):
        self.p = Memory()
        self.p.write_int32 = lambda a, n: self.p.batch_write_int32([(a, n)])
        self.w = WrenchProgression(self.p)
        self.w.enabled = True

    def test_progressive_entitlements_use_native_mod_order(self):
        for count in range(6):
            self.w.count = count
            self.assertEqual(list(self.w.entitlements().values()), [count >= n + 2 for n in range(4)])

    def test_non_ratchet_modules_get_no_code_changes(self):
        for module in (1, 2, 4, 10, 11, 31):
            symbols = Mock()
            self.assertEqual(self.w.prepare(symbols, module), [])
            symbols.get.assert_not_called()

    def test_first_copy_restores_only_wrench_button_mask(self):
        self.w.module = 3
        self.w.sites = [(0x100000, 0x30A20020)]
        self.p.batch_write_int32([(0x206328, 3), (0x206324, 0xFFFFFFFF), (0x100000, 0x30A20020)])
        self.w.sync()
        self.assertEqual(self.p.read_int32(0x100000), 0x30A20000)
        self.w.count = 1
        self.w.sync()
        self.assertEqual(self.p.read_int32(0x100000), 0x30A20020)

    def test_unknown_instruction_is_not_overwritten(self):
        self.w.module = 3
        self.w.sites = [(0x100000, 0x30A20020)]
        self.p.batch_write_int32([(0x206328, 3), (0x206324, 0xFFFFFFFF)])
        with self.assertRaises(RuntimeError):
            self.w.sync()

    def test_received_copies_override_individual_mods(self):
        c = Core(self.p)
        c.wrench.enabled = True
        c.apply_inventory(ratchet={}, clank={}, received_names=["Progressive Wrench"] * 3)
        e = c._entitlements()
        self.assertEqual([e[n] for n in range(28, 32)], [True, True, False, False])

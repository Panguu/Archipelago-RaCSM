import struct
import unittest
from unittest.mock import Mock

from ..constants import MISSION_COMPLETE_NAME, GoalOptions, SACCases
from ..core import CASE_LABELS, Core, NativeRuntime, module_counts
from ..core.inventories import AlienCodeInventory, KeycardInventory, MissionInventory
from ..locations import ALIEN_CODE_FLAGS, ALIEN_CODE_LOCATIONS, KEYCARD_LOCATIONS
from .test_runtime import TEST_BUILD, Memory
from ..constants.planets import ALL_CASES


class NativeRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.p = Memory()

    def test_vendor_selection_uses_native_modules_and_shared_cases(self):
        runtime = NativeRuntime(Memory(), Mock(), Mock())
        runtime.configure_vendors([SACCases.ASYANICA_ROOFTOPS, SACCases.GONDOLA_ASCENT])
        self.assertEqual(runtime.vendor_modules, {4, 11})
        self.assertNotIn(21, runtime.vendor_modules)

    def test_ratchet_routes_enable_vendors_but_qwark_and_gadgetbots_do_not(self):
        runtime = NativeRuntime(self.p, Mock(), Mock())
        runtime.configure_vendors(case.name for case in ALL_CASES)
        for module in (3, 9, 14, 21, 25):
            self.assertTrue(runtime.vendor_enabled_for_module(module))
        for module in (5, 18, 20, 23, 27, 28):
            self.assertFalse(runtime.vendor_enabled_for_module(module))
        for clank in (0, 1):
            self.p.batch_write_int8([(0x206C89, clank)])
            self.assertEqual(runtime.vendor_enabled_for_module(4), bool(clank))
        for qwark in (0, 1):
            self.p.batch_write_int8([(0x206CA8, qwark)])
            self.assertEqual(runtime.vendor_enabled_for_module(11), not qwark)
        runtime.configure_vendors([SACCases.ROOFTOP_DEATHTRAP, SACCases.SUCK_AND_JIVE])
        self.assertEqual(runtime.vendor_modules, set())
        runtime.configure_vendors([SACCases.HIGH_TREEHOUSE])
        self.assertTrue(runtime.vendor_enabled_for_module(31))


class MissionLabelTests(unittest.TestCase):
    def test_shared_module_reports_each_case_independently_and_deduplicates(self):
        p = Memory()
        inv = MissionInventory(p)
        inv.table_base = 0x110000
        struct.pack_into("<2I", p.data, inv.table_base + 11 * 8, 0x120000, 2)
        for i, label in enumerate((5614, 5622)):
            struct.pack_into("<I", p.data, 0x120000 + i * 96, 1)
            struct.pack_into("<I", p.data, 0x120000 + i * 96 + 12, 3)
            struct.pack_into("<I", p.data, 0x120000 + i * 96 + 60, label)
        found = inv.check_all()
        self.assertEqual(set(found), {MISSION_COMPLETE_NAME[CASE_LABELS[x]] for x in (5614, 5622)})
        for name in found:
            inv.confirm(name)
        self.assertEqual(inv.check_all(), [])
        inv.invalidate_resolved_addresses()
        self.assertEqual(inv.check_all(), [])

    def test_completion_uses_last_story_task_without_requiring_bonus_challenge(self):
        p = Memory()
        inv = MissionInventory(p)
        inv.table_base = 0x110000
        struct.pack_into("<2I", p.data, inv.table_base + 4 * 8, 0x120000, 3)
        for i, kind in enumerate((1, 1, 4)):
            struct.pack_into("<I", p.data, 0x120000 + i * 96, kind)
            struct.pack_into("<I", p.data, 0x120000 + i * 96 + 12, 3 if i == 1 else 0)
            struct.pack_into("<I", p.data, 0x120000 + i * 96 + 60, 5626)
        self.assertEqual(inv.check_all(), [MISSION_COMPLETE_NAME[CASE_LABELS[5626]]])


class AlienFlagTests(unittest.TestCase):
    def test_goal_catalog_has_every_code_and_card(self):
        self.assertEqual(len(ALIEN_CODE_LOCATIONS), 27)
        self.assertEqual(len(KEYCARD_LOCATIONS), 3)

    def test_chalice_collection_not_cards_or_door_completes_goal(self):
        p = Memory()
        cards = KeycardInventory(p)
        values = {0xAA: bytes([7]), 0xCB: bytes([0])}
        cards.flags.read = lambda index: values[index]
        cards._door_is_open = Mock(return_value=True)
        self.assertEqual(len(cards.check()), 3)
        self.assertTrue(cards.door_opened)
        self.assertFalse(cards.chalice_collected)
        core = Core(p, permanent_build=TEST_BUILD)
        core.keycards = cards
        core.goal = GoalOptions.CHALICE_OF_POWER
        core.on_goal = Mock()
        core._check_goal()
        core.on_goal.assert_not_called()
        values[0xCB] = bytes([1])
        cards.check()
        core._check_goal()
        core._check_goal()
        core.on_goal.assert_called_once()

    def test_saved_chalice_completes_only_chalice_goal(self):
        core = Core(Memory(), permanent_build=TEST_BUILD)
        core.keycards.flags.read = lambda index: bytes([1]) if index == 0xCB else bytes([0])
        core.keycards.check()
        core.on_goal = Mock()
        for goal in (GoalOptions.RATCHET_PRISON_ESCAPE, GoalOptions.ALL_GADGETBOTS,
                     GoalOptions.ALIEN_CODES, GoalOptions.QWARK_OPERA):
            core.goal = goal
            core._check_goal()
        core.on_goal.assert_not_called()
        core.goal = GoalOptions.CHALICE_OF_POWER
        core._check_goal()
        core._check_goal()
        core.on_goal.assert_called_once()
        core._goal_sent, core.goal = False, GoalOptions.ANY
        core._check_goal()
        self.assertEqual(core.on_goal.call_count, 2)

    def test_all_27_bits_and_nibble_boundaries(self):
        inv = AlienCodeInventory(Memory())
        inv.valid = True
        data = bytearray(15)
        for module in module_counts(ALIEN_CODE_FLAGS):
            data[(module - 1) // 2] |= 7 << (((module - 1) & 1) * 4)
        inv.flags.read = Mock(return_value=bytes(data))
        found = inv.check()
        self.assertEqual(len(found), 27)
        self.assertTrue(inv.all_found)
        for name in found:
            inv.confirm(name)
        self.assertEqual(inv.check(), [])
        data[0] &= ~1
        inv.flags.read.return_value = bytes(data)
        inv.check()
        self.assertFalse(inv.all_found)

    def test_invalid_binding_cannot_complete_goal(self):
        inv = AlienCodeInventory(Memory())
        inv.found = set(range(27))
        self.assertFalse(inv.all_found)

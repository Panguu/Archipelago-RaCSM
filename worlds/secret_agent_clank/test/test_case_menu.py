import struct
import unittest

from .test_runtime import Memory
from ..core.case_menu import CaseMenu, CASE_LABELS


class CaseMenuTests(unittest.TestCase):
    def setUp(self):
        self.memory = Memory()
        self.menu = CaseMenu(self.memory)
        self.menu.screen_address = 0x100000
        self.menu.parent_header = 0x100100
        self.menu.child_header = 0x100200
        struct.pack_into('<I', self.memory.data, 0x100000, 14)
        struct.pack_into('<3I', self.memory.data, 0x100100, 0x110000, 1, 0)
        struct.pack_into('<3I', self.memory.data, 0x100200, 0x110100, 1, 0)
        struct.pack_into('<I', self.memory.data, 0x110000, 0x120000)
        struct.pack_into('<I', self.memory.data, 0x110100, 0x120100)
        struct.pack_into('<I', self.memory.data, 0x1200D0, 5601)
        self.memory.data[0x1201CC:0x1201CE] = b'\x01\x01'
        struct.pack_into('<I', self.memory.data, 0x1201D0, 0x130000)
        struct.pack_into('<4I', self.memory.data, 0x130030, 3, 1, 5601, 5606)
        self.memory.write_int8 = lambda address, value: self.memory.batch_write_int8([(address, value)])

    def test_menu_lock_changes_only_selectable_byte(self):
        struct.pack_into('<I', self.memory.data, 0x13000C, 3)
        self.menu.apply_access(set())
        self.assertEqual(self.memory.writes, [(0x1201CC, 0)])
        self.assertEqual(self.memory.read_int8(0x1201CD), 1)
        self.assertEqual(self.memory.read_int32(0x13000C), 3)
        self.menu.apply_access({CASE_LABELS[5606]})
        self.assertEqual(self.memory.read_int8(0x1201CC), 1)

    def test_shared_case_unlock_uses_menu_label_not_catalog_id(self):
        self.menu.mission_table = 0x140000
        # Module 11 contains separate Clank and Qwark cases.
        struct.pack_into('<2I', self.memory.data, 0x140000 + 11 * 8, 0x150000, 2)
        for i, label in enumerate((5614, 5622)):
            struct.pack_into('<I', self.memory.data, 0x150000 + i * 96, 1)
            struct.pack_into('<I', self.memory.data, 0x150000 + i * 96 + 12, 1)
            struct.pack_into('<I', self.memory.data, 0x150000 + i * 96 + 60, label)
        changed = self.menu.unlock_owned_missions({CASE_LABELS[5622]})
        self.assertEqual(changed, {CASE_LABELS[5622]})
        self.assertEqual(self.memory.writes, [(0x150000 + 96 + 12, 2)])
        self.assertEqual(self.menu.unlock_owned_missions({CASE_LABELS[5622]}), set())

    def test_unlock_preserves_completion_after_table_snapshot(self):
        self.menu.mission_table = 0x140000
        struct.pack_into('<2I', self.memory.data, 0x140008, 0x150000, 1)
        struct.pack_into('<I', self.memory.data, 0x150000, 1)
        struct.pack_into('<I', self.memory.data, 0x15000C, 1)
        struct.pack_into('<I', self.memory.data, 0x15003C, 5611)
        read = self.memory.read_bytes

        def complete_after_snapshot(address, size):
            data = read(address, size)
            if address == 0x150000:
                struct.pack_into('<I', self.memory.data, 0x15000C, 3)
            return data

        self.memory.read_bytes = complete_after_snapshot
        self.assertEqual(self.menu.unlock_owned_missions({CASE_LABELS[5611]}), set())
        self.assertEqual(self.memory.writes, [])
        self.assertEqual(self.memory.read_int32(0x15000C), 3)

    def test_read_selected_operative_case_destination(self):
        row, = self.menu.read_entries()
        self.assertEqual((row.module_id, row.operative_mask, row.case_label), (3, 1, 5606))
        self.assertEqual(self.memory.writes, [])

    def test_does_not_read_stale_rows_outside_cases_screen(self):
        struct.pack_into('<I', self.memory.data, 0x100000, 8)
        self.assertEqual(self.menu.read_entries(), [])

    def test_rejects_rows_from_previous_operative(self):
        struct.pack_into('<I', self.memory.data, 0x1200D0, 5602)
        self.assertEqual(self.menu.read_entries(), [])

    def test_rejects_corrupt_pointer_or_flags(self):
        self.memory.data[0x1201CC] = 192
        self.assertEqual(self.menu.read_entries(), [])
        self.memory.data[0x1201CC] = 1
        struct.pack_into('<I', self.memory.data, 0x1201D0, 0xFFFFFFF0)
        self.assertEqual(self.menu.read_entries(), [])

    def test_runtime_binding_resolves_both_native_calls(self):
        getter = 0x200000
        update = 0x210000
        words = [0x3C04006D, 0x0C000000 | (getter >> 2), 0x24840EF8,
                 0x3C04006D, 0x8C5100D0, 0x0C000000 | (getter >> 2), 0x24840E50]
        struct.pack_into('<7I', self.memory.data, update, *words)
        symbols = {'g_PauseModeData': 0x654A00, 'SCRNGALACTICMAP_Update__Fv': update,
                   'SCRNGALACTICMAP_Render__Fv': update + 28,
                   'PAUSEMENU_GetCurrentItemNode__FP10tPAUSEMENU': getter}
        self.assertTrue(self.menu.bind_runtime(symbols))
        self.assertEqual(self.menu.child_header, 0x6D0EF8)
        self.assertEqual(self.menu.parent_header, 0x6D0E50)
        self.assertEqual(self.menu.screen_address, 0x654A0C)

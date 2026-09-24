import struct
import unittest
from contextlib import nullcontext

from .test_client_gameplay import GameMemory
from ..core.vendor_presentation import VendorPresentation
from ..core.address_maps import CURRENT_PLANET_ADDRESS, WEAPON_VENDOR_ITEMS, WEAPON_VENDOR_SLOTS
from ..core.address_maps import WEAPON_ARRAY_BASE_BY_PLANET


class TestVendorPresentation(unittest.TestCase):
    def setUp(self):
        self.memory = GameMemory()
        self.memory.paused = nullcontext
        self.memory.get_game_id = lambda: 'UCUS98633'
        self.view = VendorPresentation(self.memory)
        self.rows, self.icons, self.textures, menu = self.view.PROFILES[1]
        self.memory.write_int32(menu, 9)
        self.memory.write_int32(WEAPON_VENDOR_SLOTS, 2)
        self.memory.write_bytes(WEAPON_VENDOR_ITEMS, struct.pack('<2I', 4, 3))
        for i in range(2):
            self.memory.write_bytes(self.rows + i * 28, struct.pack('<7I', 4-i, 0, 1, 95+i, 0, 10000, 0))
            self.memory.write_int32(self.icons + (95+i)*4, 438+i)
            base = 0x09800000 + i*0x1000
            self.memory.write_bytes(self.textures + (438+i)*44+12, struct.pack('<II', base, base+64))
            self.memory.write_bytes(base+4, struct.pack('<4H', 4, 1, 32, 32))
            self.memory.write_bytes(base+68, struct.pack('<3H', 3, 0, 16))
            self.memory.write_int32(base+48, base+128)
            self.memory.write_int32(base+112, base+640)
            self.memory.write_bytes(base+128, bytes([i+1])*512)
            self.memory.write_bytes(base+640, bytes([i+3])*64)
        self.original = bytes(self.memory.data)

    def test_icons_restore_on_ammo_view(self):
        self.view.update(1, True, True)
        self.assertTrue(self.view.plan.installed)
        self.assertEqual(self.memory.read_bytes(0x09800080, 512), self.view.pixels)
        self.view.update(1, True, True)
        self.view.update(1, True, False)
        self.assertEqual(bytes(self.memory.data), self.original)

    def test_purchase_list_change_preserves_originals(self):
        self.view.update(1, True, True)
        self.memory.write_int32(WEAPON_VENDOR_SLOTS, 1)
        self.view.update(1, True, True)
        self.assertEqual(len(self.view.plan.edits), 2)
        self.view.restore()
        self.memory.write_int32(WEAPON_VENDOR_SLOTS, 2)
        self.assertEqual(bytes(self.memory.data), self.original)

    def test_stale_native_rows_wait_without_writes(self):
        self.memory.write_int32(self.rows, 18)
        original = bytes(self.memory.data)
        self.view.update(1, True, True)
        self.assertIsNone(self.view.plan)
        self.assertEqual(bytes(self.memory.data), original)

    def test_inactive_placeholder_does_not_block_visible_icons(self):
        self.memory.write_bytes(self.rows + 28, struct.pack('<7I', 3, 0, 0, 0, 0, 0, 0))
        self.view.update(1, True, True)
        self.assertTrue(self.view.plan.installed)
        self.assertEqual(len(self.view.plan.edits), 2)
        self.assertEqual(self.memory.read_bytes(0x09800080, 512), self.view.pixels)

    def test_loading_never_restores_departed_overlay(self):
        self.view.update(1, True, True)
        self.memory.write_int32(CURRENT_PLANET_ADDRESS, 2)
        original = bytes(self.memory.data)
        self.view.update(2, False, False)
        self.assertIsNone(self.view.plan)
        self.assertEqual(bytes(self.memory.data), original)

    def test_invalid_format_has_no_writes(self):
        self.memory.write_int16(0x09800004, 5)
        original = bytes(self.memory.data)
        self.view.update(1, True, True)
        self.assertIsNone(self.view.plan)
        self.assertEqual(bytes(self.memory.data), original)

    def test_selected_preview_uses_its_separate_texture(self):
        self.memory.write_int32(WEAPON_VENDOR_SLOTS, 1)
        self.memory.write_int32(WEAPON_ARRAY_BASE_BY_PLANET[1]+1+2*88, 0x09900000)
        self.memory.write_int32(0x09900018, 96)
        self.view.update(1, True, True)
        self.assertEqual(len(self.view.plan.edits), 4)
        self.assertEqual(self.memory.read_bytes(0x09801080, 512), self.view.pixels)

    def test_scouted_text_updates_and_restores_without_truncating_original(self):
        self.memory.write_int32(WEAPON_VENDOR_SLOTS, 1)
        self.memory.write_int32(WEAPON_ARRAY_BASE_BY_PLANET[1]+1+2*88, 0x09900000)
        self.memory.write_bytes(0x09900010, struct.pack('<II', 30, 367))
        self.memory.write_bytes(0x094A0EC0, struct.pack('<6I', 0x09901000, 1, 1, 0, 2, 1))
        self.memory.write_bytes(0x09901000, b'TDEF'+struct.pack('<II', 30, 0x09902000)+b'TDEF'+struct.pack('<II', 367, 0x09903000))
        self.memory.write_bytes(0x09903000, b'Original weapon description. '*12+b'\0')
        self.view.reward_for_id = lambda identity: ('Bolts', 'PSPPlayer')
        before = bytes(self.memory.data)
        self.view.update(1, True, True)
        self.assertFalse(self.view.failed)
        self.assertIn(b'Bolts', self.memory.read_bytes(0x09903000, 100))
        self.view.update(1, True, True)
        self.view.reward_for_id = lambda identity: ('Progressive Armour', 'Player Two')
        self.view.update(1, True, True)
        self.assertFalse(self.view.failed)
        self.assertIn(b'Progressive Armour', self.memory.read_bytes(0x09903000, 100))
        self.view.restore()
        self.assertEqual(bytes(self.memory.data), before)

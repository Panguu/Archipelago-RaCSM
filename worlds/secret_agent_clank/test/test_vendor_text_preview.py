"""Native vendor text preview regression tests."""
import struct
import unittest
from pathlib import Path

from ..core.notifications import ItemNotifications
from ..core.patches.vendor_text_preview import VendorTextPreview
from ..core.symbols import RuntimeSymbols
from .test_native_capture_plans import CaptureMemory


class VendorTextPreviewTests(unittest.TestCase):
    def test_text_hooks_restore_capture_without_touching_prices(self):
        path = Path(__file__).parents[1] / ".research/vendor_separation_baseline.bin"
        if not path.exists():
            self.skipTest("Local vendor capture unavailable")
        p = CaptureMemory()
        p.data[:] = path.read_bytes()
        p.get_game_id = lambda: "SCUS-97623"
        symbols = RuntimeSymbols.parse(p.data[:0x1000000], 0)
        notification = ItemNotifications(p)
        self.assertTrue(notification.bind(symbols))
        struct.pack_into("<I", p.data, notification.binding[1], 0)
        preview = VendorTextPreview(p)
        preview.prepare(symbols, title="Progressive Wrench", description="For Pangu")
        before = bytes(p.data)
        price = p.read_int32(preview.vendor.price_addr)
        preview.apply()
        self.assertEqual(p.read_int32(preview.vendor.price_addr), price)
        preview.restore()
        self.assertEqual(bytes(p.data), before)

    def test_text_is_bounded_and_cannot_inject_native_color_codes(self):
        data = VendorTextPreview._text("X\x90\x03" + "A" * 200, 96)
        self.assertEqual(len(data), 96)
        self.assertEqual(data[-1], 0)
        self.assertNotIn(b"\x90", data)

    def test_progression_color_prefix_and_white_reset(self):
        orange = VendorTextPreview._text("Reward", 96, color=2)
        white = VendorTextPreview._text("Reward", 96, color=1)
        self.assertTrue(orange.startswith(b"\x90\x02Reward\x90\x01\0"))
        self.assertTrue(white.startswith(b"\x90\x01Reward\x90\x01\0"))

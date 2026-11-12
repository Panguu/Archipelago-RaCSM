import unittest

from ..core.patches.vendor_text import VendorTextLayout


class VendorTextTests(unittest.TestCase):

    def test_text_is_bounded_and_cannot_inject_native_color_codes(self):
        data = VendorTextLayout._text("X\x90\x03" + "A" * 200, 96)
        self.assertEqual(len(data), 96)
        self.assertEqual(data[-1], 0)
        self.assertNotIn(b"\x90", data)

    def test_progression_color_prefix_and_white_reset(self):
        orange = VendorTextLayout._text("Reward", 96, color=2)
        white = VendorTextLayout._text("Reward", 96, color=1)
        self.assertTrue(orange.startswith(b"\x90\x02Reward\x90\x01\0"))
        self.assertTrue(white.startswith(b"\x90\x01Reward\x90\x01\0"))

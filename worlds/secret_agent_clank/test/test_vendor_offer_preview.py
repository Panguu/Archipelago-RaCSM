"""Captured vendor insertion and restoration checks; no live PINE writes."""
import unittest
from pathlib import Path

from ..core.patches.vendor_offer_preview import VendorOfferPreview
from ..core.symbols import RuntimeSymbols
from .test_native_capture_plans import CaptureMemory


class VendorOfferPreviewTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).parents[1] / ".research/vendor_separation_baseline.bin"
        if not path.exists():
            self.skipTest("Local vendor capture unavailable")
        self.pine = CaptureMemory()
        self.pine.data[:] = path.read_bytes()
        self.pine.get_game_id = lambda: "SCUS-97623"
        self.symbols = RuntimeSymbols.parse(self.pine.data[:0x1000000], 0)
        self.preview = VendorOfferPreview(self.pine)

    def test_append_keeps_original_rows_and_restores_all_bytes(self):
        self.preview.prepare(self.symbols, source_index=0)
        before = bytes(self.pine.data)
        original = self.preview.vendor.read_items()
        self.preview.apply()
        rows = self.preview.read()
        self.assertEqual(rows[:-1], original)
        self.assertEqual(rows[-1][1:], original[0][1:])
        buy = self.symbols["SCRNVENDOR_ProcessPurchase__Fv"]
        self.assertEqual(self.pine.read_bytes(buy, 8), self.preview.RETURN)
        self.preview.restore()
        self.assertEqual(bytes(self.pine.data), before)

    def test_unknown_row_type_rejected_without_writing(self):
        import struct
        self.preview.vendor.bind_runtime(self.symbols)
        pointer, _, _ = self.preview.vendor._native_header()
        struct.pack_into("<I", self.pine.data, pointer + 12, 99)
        before = bytes(self.pine.data)
        with self.assertRaises(RuntimeError):
            self.preview.prepare(self.symbols, source_index=0)
        self.assertEqual(bytes(self.pine.data), before)
        self.assertEqual(self.preview.patches, [])

    def test_changed_module_rejects_apply(self):
        import struct
        self.preview.prepare(self.symbols, source_index=0)
        struct.pack_into("<I", self.pine.data, 0x206328, 22)
        before = bytes(self.pine.data)
        with self.assertRaises(RuntimeError):
            self.preview.apply()
        self.assertEqual(bytes(self.pine.data), before)

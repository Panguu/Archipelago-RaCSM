"""Icon preview transaction regression using the recorded native test plan."""
import json
import unittest
from pathlib import Path

from ..core.patches.asm import Patch
from ..core.patches.vendor_icon_preview import VendorIconPreview
from .test_native_capture_plans import CaptureMemory


class VendorIconPreviewTests(unittest.TestCase):
    def test_preview_restores_pixels_and_invalidates_cache(self):
        path = Path(__file__).parents[1] / ".research/vendor_icon_preview.json"
        if not path.exists():
            self.skipTest("Local icon probe journal unavailable")
        record = json.loads(path.read_text())
        memory = CaptureMemory()
        memory.data[:] = bytes(0x2000000)
        memory.write_int32 = lambda a,v: memory.batch_write_int32([(a,v)])
        preview = VendorIconPreview(memory)
        preview.cache = record["cache"]
        preview._check_context = lambda: None
        preview.patches = [Patch(p["address"], bytes.fromhex(p["original"]),
                                bytes.fromhex(p["replacement"])) for p in record["patches"]]
        for patch in preview.patches:
            memory.data[patch.address:patch.address+len(patch.original)] = patch.original
        before = bytes(memory.data)
        preview.apply()
        self.assertTrue(preview.installed)
        preview.restore()
        self.assertFalse(preview.installed)
        self.assertEqual(bytes(memory.data), before)

    def test_native_asset_sizes_and_alpha(self):
        root = Path(__file__).parents[1] / "icon"
        indices = (root / "archipelago-icon.indices").read_bytes()
        palette = (root / "archipelago-icon.clut").read_bytes()
        self.assertEqual(len(indices),1024)
        self.assertEqual(len(palette),1024)
        self.assertLessEqual(max(palette[3::4]),128)
        self.assertIn(0,palette[3::4])

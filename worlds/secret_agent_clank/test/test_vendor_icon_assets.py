import unittest
from pathlib import Path



class VendorIconAssetTests(unittest.TestCase):

    def test_native_asset_sizes_and_alpha(self):
        root = Path(__file__).parents[1] / "icon"
        indices = (root / "archipelago-icon.indices").read_bytes()
        palette = (root / "archipelago-icon.clut").read_bytes()
        self.assertEqual(len(indices),1024)
        self.assertEqual(len(palette),1024)
        self.assertLessEqual(max(palette[3::4]),128)
        self.assertIn(0,palette[3::4])

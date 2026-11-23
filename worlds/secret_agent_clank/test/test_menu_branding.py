import io
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import zipfile

from ..patcher import menu_branding as branding
from ..patcher.filenames import IMAGE_ARCHIVE
from ..patcher.iso import ISOImage


class TestMenuBranding(unittest.TestCase):
    def test_unknown_background_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unexpected USA"):
            branding.patch_background(bytes(381960))

    def test_unknown_brand_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown menu branding"):
            branding.patch_background(b"", "other")

    @unittest.skipUnless(os.environ.get("SAC_TEST_ISO"), "Set SAC_TEST_ISO for real-disc verification")
    def test_multiworldgg_changes_only_pic1_and_preserves_background_colours(self):
        with Path(os.environ["SAC_TEST_ISO"]).open("rb") as stream:
            data = ISOImage(stream).read_file(IMAGE_ARCHIVE)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            original = archive.read(branding.MEMBER)
        result = branding.patch_background(original, "multiworldgg")
        self.assertEqual(result[:branding.PIXELS], original[:branding.PIXELS])
        self.assertEqual(result[branding.PALETTE + 1024:], original[branding.PALETTE + 1024:])
        changed_background = 0
        for offset in range(512 * 256):
            y, x = divmod(offset, 512)
            if 36 <= x < 300 and 189 <= y < 211:
                continue
            a = branding.palette_offset(original[branding.PIXELS + offset])
            b = branding.palette_offset(result[branding.PIXELS + offset])
            if original[a:a+4] != result[b:b+4]:
                changed_background += 1
        self.assertLess(changed_background, 256)
        self.assertNotEqual(result, branding.patch_background(original))

    def test_zip_replacement_preserves_other_records_and_has_no_duplicate(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("before", b"unchanged first member")
            archive.writestr(branding.MEMBER, b"old background")
            archive.writestr("after", b"unchanged last member")
        original = stream.getvalue()
        with patch.object(branding, "patch_background", return_value=b"new background"):
            result = branding.patch_menu_archive(original)
        with zipfile.ZipFile(io.BytesIO(original)) as old, zipfile.ZipFile(io.BytesIO(result)) as new:
            self.assertIsNone(new.testzip())
            self.assertEqual(new.namelist().count(branding.MEMBER), 1)
            self.assertEqual(new.read(branding.MEMBER), b"new background")
            for name in ("before", "after"):
                self.assertEqual(old.getinfo(name).header_offset, new.getinfo(name).header_offset)
                self.assertEqual(old.read(name), new.read(name))
            self.assertEqual(original[:old.start_dir], result[:old.start_dir])

    @unittest.skipUnless(os.environ.get("SAC_TEST_ISO"), "Set SAC_TEST_ISO for real-disc verification")
    def test_real_disc_changes_only_logo_pixels(self):
        with Path(os.environ["SAC_TEST_ISO"]).open("rb") as stream:
            data = ISOImage(stream).read_file(IMAGE_ARCHIVE)
        result = branding.patch_menu_archive(data)
        with zipfile.ZipFile(io.BytesIO(data)) as old, zipfile.ZipFile(io.BytesIO(result)) as new:
            self.assertIsNone(new.testzip())
            self.assertEqual(set(old.namelist()), set(new.namelist()))
            for name in old.namelist():
                if name != branding.MEMBER:
                    self.assertEqual(old.read(name), new.read(name), name)
            before, after = old.read(branding.MEMBER), new.read(branding.MEMBER)
        self.assertEqual(len(before), len(after))
        changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
        self.assertGreater(len(changed), 1000)
        for index in changed:
            y, x = divmod(index - branding.PIXELS, branding.WIDTH)
            self.assertTrue(branding.LOGO_X <= x <= branding.LOGO_X + branding.LOGO_WIDTH)
            self.assertTrue(branding.LOGO_Y <= y <= branding.LOGO_Y + branding.LOGO_HEIGHT)
        with self.assertRaises(ValueError):
            branding.patch_background(after)

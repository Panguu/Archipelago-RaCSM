import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

import Utils

from worlds.Files import AutoPatchRegister
from ..patcher.build import make_patch
from ..patcher.container import SACPatch
from ..patcher.filenames import EXECUTABLE, LEVEL_FILES
from ..patcher.iso import sha256_file, write_patched_iso
from ..patcher.menu_branding import app_branding
from .test_iso import fixture

NEW_LEVEL = b"SNR2" + bytes(range(256)) * 20
# The test disc has no IMAGE.ZIP, so the executable stands in as the branded file.
BRANDED_EXECUTABLE = {"archipelago": b"\x7fELFAP", "multiworldgg": b"\x7fELFMWGG"}


def fixture_patch(folder: Path) -> tuple[SACPatch, Path, dict[str, Path]]:
    """A patch that swaps LEVEL1 for every brand, plus a per-brand executable.

    Returns (patch, clean ISO, {branding: expected patched ISO}).
    """
    clean = folder / "clean.iso"
    clean.write_bytes(fixture())
    expected = {}
    for branding, executable in BRANDED_EXECUTABLE.items():
        expected[branding] = folder / f"expected-{branding}.iso"
        write_patched_iso(clean, expected[branding], {LEVEL_FILES[1]: NEW_LEVEL, EXECUTABLE: executable})
    patch = make_patch("sac-iso-v1-0123456789abcdef01234567", sha256_file(clean),
                       {branding: sha256_file(path) for branding, path in expected.items()},
                       {LEVEL_FILES[1]: (b"SNR2abcd", NEW_LEVEL)},
                       {branding: {EXECUTABLE: (b"\x7fELF", executable)}
                        for branding, executable in BRANDED_EXECUTABLE.items()})
    return patch, clean, expected


class TestSACPatch(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        self.patch, self.clean, self.expected = fixture_patch(self.folder)
        self.files = sorted(p.name for p in self.folder.iterdir())

    def test_registered_handler(self):
        self.assertIs(AutoPatchRegister.get_handler("example.apsac"), SACPatch)

    def test_write_read_and_apply_each_branding(self):
        patch_file = self.folder / "slot.apsac"
        self.patch.player, self.patch.player_name = 3, "Agent"
        self.patch.write(str(patch_file))

        reread = SACPatch(str(patch_file))
        reread.read()
        self.assertEqual((reread.player, reread.player_name), (3, "Agent"))
        self.assertEqual(reread.brandings, ["archipelago", "multiworldgg"])
        for branding, expected in self.expected.items():
            with self.subTest(branding=branding):
                progress = []
                out = self.folder / f"out-{branding}.iso"
                reread.apply(self.clean, out, branding, lambda *step: progress.append(step))
                self.assertEqual(out.read_bytes(), expected.read_bytes())
                self.assertEqual(progress[-1][1], 1.0)
        self.assertEqual(self.clean.read_bytes(), fixture())

        with zipfile.ZipFile(patch_file) as archive:
            manifest = json.loads(archive.read("archipelago.json"))
            self.assertEqual(manifest["procedure"], "custom")
            self.assertEqual(manifest["result_file_ending"], ".iso")

    def test_unknown_branding(self):
        with self.assertRaisesRegex(ValueError, "no other menu"):
            self.patch.apply(self.clean, self.folder / "out.iso", "other")

    def test_choose_branding_follows_the_app(self):
        with mock.patch.object(Utils, "instance_name", "MultiworldGG", create=True):
            self.assertEqual(app_branding(), "multiworldgg")
            self.assertEqual(self.patch.choose_branding(), "multiworldgg")
            # A build without the MultiworldGG menu falls back to Archipelago's.
            del self.patch.build["result_sha256"]["multiworldgg"]
            self.assertEqual(self.patch.choose_branding(), "archipelago")
        self.assertFalse(hasattr(Utils, "instance_name"))  # plain Archipelago has none
        self.assertEqual(app_branding(), "archipelago")

    def test_never_overwrites(self):
        with self.assertRaises(FileExistsError):
            self.patch.apply(self.clean, self.clean, "archipelago")

    def test_wrong_iso(self):
        with self.assertRaisesRegex(ValueError, "clean copy"):
            self.patch.apply(self.expected["archipelago"], self.folder / "out.iso", "archipelago")
        self.assertFalse((self.folder / "out.iso").exists())

    def test_damaged_patch(self):
        wrong = make_patch("x", "", {}, {LEVEL_FILES[1]: (b"SNR2abcd", b"SNR2xxxx")}, {})
        self.patch.deltas["files/00.bsdiff4"] = wrong.deltas["files/00.bsdiff4"]
        with self.assertRaisesRegex(ValueError, "damaged"):
            self.patch.apply(self.clean, self.folder / "out.iso", "archipelago")
        self.assertEqual(sorted(p.name for p in self.folder.iterdir()), self.files)

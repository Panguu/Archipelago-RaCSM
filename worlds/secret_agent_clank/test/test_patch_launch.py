import asyncio
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import Utils

from ..patcher import launch
from .test_container import fixture_patch
from ..patcher.container import SACPatch


class TestPatchLaunch(unittest.TestCase):
    def test_brand_variants_have_distinct_cached_iso_paths(self):
        patch = SACPatch()
        patch.build = {"build_id": "sac-iso-v1-0123456789abcdef01234567"}
        with mock.patch.object(launch, "user_path", side_effect=lambda path: path):
            self.assertNotEqual(launch.patched_iso_path(patch, "archipelago"),
                                launch.patched_iso_path(patch, "multiworldgg"))

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        patch, self.clean, self.expected = fixture_patch(self.folder)
        patch.player, patch.player_name = 1, "Agent"
        self.patch_file = self.folder / "slot.apsac"
        patch.write(str(self.patch_file))
        self.target = self.folder / "patched.iso"

    def prepare(self, clean_iso_path):
        with mock.patch.object(launch, "patched_iso_path", return_value=self.target), \
                mock.patch.object(launch, "clean_iso_path", clean_iso_path):
            return asyncio.run(launch.prepare_iso(str(self.patch_file), gui=False))

    def test_multiworldgg_gets_its_menu(self):
        with mock.patch.object(Utils, "instance_name", "MultiworldGG", create=True):
            _, iso = self.prepare(mock.Mock(return_value=str(self.clean)))
        self.assertEqual(iso.read_bytes(), self.expected["multiworldgg"].read_bytes())

    def test_patches_once_then_reuses_the_iso(self):
        patch, iso = self.prepare(mock.Mock(return_value=str(self.clean)))
        self.assertEqual((iso, patch.player_name), (self.target, "Agent"))
        self.assertEqual(iso.read_bytes(), self.expected["archipelago"].read_bytes())

        # The next seed on the same build shouldn't need the clean ISO at all.
        not_called = mock.Mock(side_effect=AssertionError("asked for the clean ISO"))
        self.assertEqual(self.prepare(not_called)[1], self.target)

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from ..patcher import SACPatch, load_runtime_build
from ..patcher.filenames import EXECUTABLE, MODULE_FILES, IMAGE_ARCHIVE
from ..world import SecretAgentClankWorld
from Utils import local_path, read_apignore


class TestISORelease(unittest.TestCase):
    def test_release_filters_keep_patch_resources_and_exclude_private_disc_data(self):
        root = Path(__file__).resolve().parents[1]
        global_spec = read_apignore(local_path("data", "GLOBAL.apignore"))
        for filename in (".apignore", "apworld.ignore"):
            with self.subTest(builder=filename):
                spec = global_spec + read_apignore(root / filename)
                for path in (".research/module-1.rel", ".research/capture.bin",
                             ".client_state/session.json", "build/game.iso", "game.iso", "module-1.rel"):
                    self.assertTrue(spec.match_file(path), path)
                for path in ("data/sac-runtime.json", "data/patch/sac-build.json", "data/patch/files/00.bsdiff4"):
                    self.assertFalse(spec.match_file(path), path)

    def test_each_slot_gets_its_own_file_with_the_same_patch(self):
        with tempfile.TemporaryDirectory() as directory:
            for player in (1, 2):
                world = SecretAgentClankWorld.__new__(SecretAgentClankWorld)
                world.player = player
                world.multiworld = SimpleNamespace(get_out_file_name_base=lambda p: f"seed-P{p}",
                                                   get_player_name=lambda p: f"Agent{p}")
                world.generate_output(directory)
            first, second = SACPatch(str(Path(directory, "seed-P1.apsac"))), SACPatch(str(Path(directory, "seed-P2.apsac")))
            first.read()
            second.read()

        self.assertEqual((first.player_name, second.player_name), ("Agent1", "Agent2"))
        self.assertEqual((first.build, first.deltas), (second.build, second.deltas))
        self.assertEqual(first.build["build_id"], load_runtime_build()["build_id"])
        self.assertEqual({file["path"] for file in first.build["files"]}, {EXECUTABLE, IMAGE_ARCHIVE, *MODULE_FILES.values()})

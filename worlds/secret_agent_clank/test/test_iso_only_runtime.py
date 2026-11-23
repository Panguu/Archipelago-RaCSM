import json
import os
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from ..core import Core
from ..core.permanent_runtime import PermanentRuntime
from ..core.patches import LocationHooks, PatchSet, StartingCase
from ..core.patches.patch import Patch
from ..core.patches.loader_state import LoaderStateReader
from .test_runtime import Memory
from ..client.game_worker import GameRuntime
from ..core.patches.identity import WrongPatchedGame
from ..patcher.filenames import EXECUTABLE, MODULE_FILES
from ..patcher.iso import ISOImage
from ..core.patches.snr2 import resident_exports
from ..core.patches.level_build import compile_level
from ..core.patches.frontend_build import compile_frontend


class ISOOnlyRuntimeTests(unittest.TestCase):
    def test_none_build_cannot_disable_the_worker_identity_guard(self):
        memory = Memory()
        memory.connect = Mock()
        memory.disconnect = Mock()
        memory.set_slot = Mock()
        memory.get_game_id = Mock(return_value="SCUS-97623")
        with patch("worlds.secret_agent_clank.client.game_worker.Pine", return_value=memory):
            worker = GameRuntime(Mock(), permanent_build=None)
        self.assertIsNotNone(worker.permanent_build)
        worker.core.native_runtime.verify = Mock(side_effect=WrongPatchedGame("clean ISO"))
        with self.assertRaises(WrongPatchedGame):
            worker.dispatch("connect", 28011)
        self.assertFalse(worker.connected)
        self.assertEqual(memory.writes, [])
        memory.disconnect.assert_called_once()

    def test_default_core_uses_verified_disc_runtime(self):
        core = Core(Memory())
        self.assertIsInstance(core.native_runtime, PermanentRuntime)
        self.assertTrue(core.location_hooks.permanent)

    def test_builders_and_loader_have_no_live_installation_api(self):
        for cls, names in ((Patch, ("apply",)), (PatchSet, ("apply",)),
                           (Core, ("_bind_native_locations",)),
                           (LocationHooks, ("install", "install_at_loader_gate", "_install_plan", "restore")),
                           (StartingCase, ("apply", "service", "close")),
                           (LoaderStateReader, ("arm", "release"))):
            for name in names:
                with self.subTest(cls=cls.__name__, method=name):
                    self.assertFalse(hasattr(cls, name))


@unittest.skipUnless(os.environ.get("SAC_TEST_ISO") and os.environ.get("SAC_TEST_BUILD")
                     and os.environ.get("SAC_TEST_COMPILE"), "Set ISO, build and compile flags for compatibility audit")
class ISOCompilerCompatibilityTests(unittest.TestCase):
    def test_existing_iso_payload_and_bindings_are_unchanged(self):
        root = Path(os.environ["SAC_TEST_BUILD"])
        build = json.loads((root / "data" / "sac-runtime.json").read_text())
        with Path(os.environ["SAC_TEST_ISO"]).open("rb") as source:
            iso = ISOImage(source)
            imports = resident_exports(iso.read_file(EXECUTABLE))
            for module, filename in MODULE_FILES.items():
                with self.subTest(module=module):
                    record = build["modules"][str(module)]
                    args = dict(identity=bytes.fromhex(record["identity"]), with_bindings=True)
                    if module == 0:
                        compiled, bindings = compile_frontend(iso.read_file(filename), imports, **args)
                    else:
                        compiled, bindings = compile_level(iso.read_file(filename), imports,
                                                           module, record["vendor"], **args)
                    self.assertEqual(compiled, (root / f"module-{module}.rel").read_bytes())
                    self.assertEqual(bindings, record)

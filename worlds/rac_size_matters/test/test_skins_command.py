import unittest
from dataclasses import replace
from types import SimpleNamespace

from ..client.worker import GameWorker
from ..core import address_maps
from ..core.native_runtime import NativeRuntime
from ..core.patches import PatchOptions
from ..core.skins import Skin, SkinInventory
from .test_native_patches import Memory


class SkinsCommandTests(unittest.TestCase):
    def test_toggling_requests_a_fresh_level(self):
        for enabled in (False, True):
            self.check_reload(enabled)

    def check_reload(self, enabled):
        memory = Memory()
        planet = SimpleNamespace(is_ready=True, starting_planet_id=None)
        runtime = NativeRuntime(memory, SimpleNamespace(planet=planet, native_plan=None),
                                lambda _: None, lambda _: None, patch_options=PatchOptions(vendor=False, skins=enabled))
        runtime.enabled = True
        runtime.module = 1
        runtime.starting_planet.service = lambda _: None
        runtime.gate.arm = lambda: None
        runtime.gate.held_module = lambda: None
        memory.write_int32(runtime.gate.STATE, 6)
        memory.write_int32(address_maps.NEW_PLANET_START_LOAD_ADDR, 0xFFFFFFFF)
        runtime.patch_options = replace(runtime.patch_options, skins=not enabled)
        self.assertTrue(runtime.tick())
        self.assertEqual(memory.read_int32(address_maps.NEW_PLANET_START_LOAD_ADDR), 1)

    def test_off_equips_default_and_on_restores_patch(self):
        memory = Memory()
        skin = SkinInventory(memory)
        skin.set(Skin.TUXEDO_RATCHET)
        worker = GameWorker.__new__(GameWorker)
        worker.pine_connected = True
        worker._wiring = SimpleNamespace(native=SimpleNamespace(patch_options=PatchOptions()), skin=skin)
        worker._multiplayer_skins_override = None
        worker._set_skin_patch(False)
        self.assertFalse(worker._wiring.native.patch_options.skins)
        self.assertFalse(worker._wiring.native.patch_options.multiplayer_skins)
        self.assertEqual(skin.equipped, Skin.DEFAULT.equip_id)
        self.assertEqual(skin.get(), Skin.DEFAULT)
        worker._set_skin_patch(True)
        self.assertTrue(worker._wiring.native.patch_options.skins)
        self.assertTrue(worker._wiring.native.patch_options.multiplayer_skins)
        self.assertEqual(skin.get(), Skin.DEFAULT)

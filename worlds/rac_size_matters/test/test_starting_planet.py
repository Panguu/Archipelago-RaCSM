"""Execute retail frontend excerpts: new saves, launch exits and save resumes."""
import json
import unittest
from pathlib import Path
from unittest.mock import Mock

from ..core.patches import starting_planet as sp
from ..core.patches.loader_gate import LoaderGate
from ..core.planets import PlanetInventory
from .test_native_patches import CPU, Memory

FIXTURE = json.loads((Path(__file__).parent / "fixtures/starting_planet_us.json").read_text())
BASE = FIXTURE["base"]
SAVE = 0x1800000


class StartingPlanetTests(unittest.TestCase):
    def memory(self):
        p = Memory()
        for address, data in FIXTURE["segments"]:
            p.write_bytes(address, bytes.fromhex(data))
        for address, value in ((LoaderGate.STATE, 6), (LoaderGate.TARGET, 0),
                               (0x1F4C76C, 0), (LoaderGate.HANDLE, 1),
                               (LoaderGate.MODULES + 0x418 + 4, BASE),
                               (LoaderGate.MODULES + 0x418 + 8, 1),
                               (0xF36A1C, SAVE)):
            p.write_int32(address, value)
        p.writes.clear()
        return p

    def test_new_save_and_both_hardcoded_exits(self):
        for planet in sp.ELIGIBLE:
            with self.subTest(planet=planet):
                p = self.memory()
                plan = sp.prepare(p, BASE, planet)
                plan.install()
                c = CPU(p)
                c.r[4], c.r[5] = SAVE, 1
                stubs = {address: lambda c: None for address in
                         (0x1EC6DA8, 0x1EC62F4, 0xF12258, 0xF126D8, 0xF11E68)}
                stubs[0xF11AA8] = lambda c: c.r.__setitem__(2, 0)
                c.run(BASE + sp.INIT, stop=BASE + sp.SAVE + 16, stubs=stubs)
                self.assertEqual(p.read_int32(SAVE + 0x1C6C), planet)
                self.assertEqual(c.r[16], 1)  # Other new-save defaults remain 1.
                self.assertEqual(p.read_int32(SAVE + 0x1C74), 0)
                for offset in sp.TRAVEL:
                    c = CPU(p)
                    launches = []
                    c.run(BASE + offset, stop=BASE + offset + 12,
                          stubs={BASE + sp.CHANGE_LEVEL:
                                 lambda c: launches.append((c.r[4], c.r[5]))})
                    self.assertEqual(launches, [(planet, 1)])
                # The memory-card New Game route reads the initialized save.
                c = CPU(p)
                launches = []
                c.run(0xF2974C, stop=0xF29760,
                      stubs={BASE + sp.CHANGE_LEVEL: lambda c: launches.append(c.r[4])})
                self.assertEqual(launches, [planet])
                plan.restore()
                for edit in plan.edits:
                    self.assertEqual(p.read_bytes(edit.address, len(edit.original)), edit.original)

    def test_existing_save_skips_destination_initialization(self):
        p = self.memory()
        sp.prepare(p, BASE, 23).install()
        p.write_int32(SAVE + 0x1C6C, 7)
        c = CPU(p)
        c.r[4], c.r[5] = SAVE, 0
        c.run(BASE + sp.INIT, stubs={0xF11AA8: lambda c: c.r.__setitem__(2, 1)})
        self.assertEqual(p.read_int32(SAVE + 0x1C6C), 7)
        # Load Game uses the getter, not either hard-coded new-save exit.
        c = CPU(p)
        launches = []
        c.run(0xF27AB4, stop=0xF27AC8,
              stubs={0xF120E8: lambda c: c.r.__setitem__(2, p.read_int32(SAVE + 0x1C6C)),
                     BASE + sp.CHANGE_LEVEL: lambda c: launches.append((c.r[4], c.r[5]))})
        self.assertEqual(launches, [(7, 0)])

    def test_service_reconfigure_reset_disable_and_unload(self):
        p = self.memory()
        patch = sp.StartingPlanet(p, Mock())
        patch.service(2)
        p.writes.clear()
        patch.service(2)
        self.assertEqual(p.writes, [])
        patch.service(23)
        self.assertEqual(p.read_int32(BASE + sp.TRAVEL[0]), 0x24040017)
        patch.plan.restore()  # Simulate a pristine frontend savestate reload.
        patch.service(23)
        self.assertTrue(patch.plan.installed)
        patch.service(None)
        self.assertIsNone(patch.plan)
        patch.service(1)
        self.assertIsNone(patch.plan)
        patch.service(3)
        p.write_int32(0x1F4C76C, 3)
        p.writes.clear()
        patch.close()
        self.assertEqual(p.writes, [])

    def test_signature_failure_and_write_failure(self):
        p = self.memory()
        p.write_int32(BASE + sp.TRAVEL[1], 0)
        p.writes.clear()
        with self.assertRaises(RuntimeError):
            sp.prepare(p, BASE, 2)
        self.assertEqual(p.writes, [])
        p = self.memory()
        plan = sp.prepare(p, BASE, 2)
        p.fail_once = plan.edits[-1].address
        with self.assertRaises(OSError):
            plan.install()
        for edit in plan.edits:
            self.assertEqual(p.read_bytes(edit.address, len(edit.original)), edit.original)

    def test_pokitaru_arrival_is_never_redirected(self):
        p = self.memory()
        planet = PlanetInventory(p, Mock(), Mock())
        planet.set_starting_planet(23)
        planet._ready_on_planet(1)
        self.assertTrue(planet.is_ready)
        self.assertEqual(planet.planet_id, 1)
        self.assertFalse(any(address == 0x1F4A744 for address, _ in p.writes))

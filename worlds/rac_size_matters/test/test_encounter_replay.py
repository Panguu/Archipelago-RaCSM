"""Replay boundaries must preserve checks and independently completed puzzles."""

import json
import unittest
from dataclasses import fields
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ..constants import Rac5CutsceneLocations as Missions
from ..constants.shrink_ray import SHRINK_RAY_PUZZLE_BITS
from ..core import address_maps
from ..core.missions import MissionInventory
from ..core.native_runtime import NativeRuntime
from ..core.patches import PatchOptions
from ..core.patches import quodrona_replay
from ..core.patches.asm import jump
from ..core.shrink_ray import ShrinkRaySkipInventory
from .test_shrink_ray import ShrinkMemory
from .test_native_patches import CPU


class EncounterReplayTests(unittest.TestCase):
    def test_reset_preserves_history_other_planets_and_puzzle_flags_in_each_region(self):
        original_game = address_maps.GAME_ID
        try:
            for game in address_maps.SUPPORTED_GAMES:
                address_maps.select_game(game)
                with self.subTest(game=game):
                    p = ShrinkMemory()
                    missions = MissionInventory(p)
                    challax = address_maps.save_address(0x1F4B3D0)
                    quodrona = address_maps.save_address(0x1F4B3D6)
                    p.write_int16(challax, 0xFFFF)
                    p.write_int16(quodrona, 0xFFFF)
                    p.write_int16(address_maps.SHRINK_RAY_GATE_ADDRESS, 0xFFFF)
                    p.writes.clear()

                    self.assertEqual(set(missions.prepare_replay(7)), {Missions.CHALLAX_ENTER, Missions.CHALLAX_EXPLORE})
                    self.assertEqual(p.read_int16(challax), 1)
                    self.assertEqual(p.read_int16(quodrona), 0xFFFF)
                    self.assertEqual(missions.prepare_replay(10), [])
                    self.assertEqual(p.read_int16(quodrona), 0xFFFF)
                    self.assertTrue(missions.get(Missions.QUODRONA_GOAL))
                    self.assertEqual(p.read_int16(address_maps.SHRINK_RAY_GATE_ADDRESS), 0xFFFF)
                    self.assertEqual({addr for addr, _ in p.writes}, {challax})

                    # Replaying is allowed to finish. Clearing it again on the
                    # next visit must never award a second completion.
                    missions.set(Missions.CHALLAX_EXPLORE, True)
                    missions.set(Missions.QUODRONA_CLONE, True)
                    self.assertEqual(missions.prepare_replay(7), [])
                    self.assertEqual(missions.prepare_replay(10), [])
                    self.assertIn(Missions.CHALLAX_EXPLORE, missions.completed)
                    p.writes.clear()
                    for planet in (1, 6, 15, 21, 24):
                        self.assertEqual(missions.prepare_replay(planet), [])
                    self.assertEqual(p.writes, [])
        finally:
            address_maps.select_game(original_game)

    def test_reset_happens_before_loader_release_and_not_on_gameplay_polls(self):
        p = ShrinkMemory()
        missions = MissionInventory(p)
        missions.set(Missions.CHALLAX_EXPLORE, True)
        planet = SimpleNamespace(is_ready=False, planet_id=7, starting_planet_id=None)
        vendor = SimpleNamespace(planet=planet, native_plan=None)
        options = PatchOptions(**{field.name: False for field in fields(PatchOptions)})
        sent = Mock()
        runtime = NativeRuntime(p, vendor, sent, Mock(), patch_options=options, missions=missions)
        runtime.enabled = True
        runtime.allowed_locations = {Missions.CHALLAX_EXPLORE}
        runtime.starting_planet.service = Mock()
        runtime.gate.arm = Mock()
        runtime.gate.held_module = Mock(return_value=(7, 0xD00000))

        def release():
            self.assertFalse(missions.get(Missions.CHALLAX_EXPLORE))
            self.assertIn(Missions.CHALLAX_EXPLORE, missions.completed)

        runtime.gate.release = Mock(side_effect=release)
        p.write_int32(runtime.gate.STATE, 4)
        self.assertTrue(runtime.tick())
        runtime.gate.release.assert_called_once()
        sent.assert_called_once_with(Missions.CHALLAX_EXPLORE)
        runtime.gate.held_module.return_value = None
        p.write_int32(runtime.gate.STATE, 6)
        p.write_int32(runtime.gate.TARGET, 7)
        p.write_int32(address_maps.CURRENT_PLANET_ADDRESS, 7)
        missions.set(Missions.CHALLAX_EXPLORE, True)
        self.assertFalse(runtime.tick())
        self.assertTrue(missions.get(Missions.CHALLAX_EXPLORE))

    def test_failed_patch_installation_does_not_reset_progress(self):
        p = ShrinkMemory()
        missions = MissionInventory(p)
        missions.set(Missions.CHALLAX_EXPLORE, True)
        options = {field.name: False for field in fields(PatchOptions)}
        options['armour_pickup'] = True
        runtime = NativeRuntime(p, SimpleNamespace(planet=SimpleNamespace()), Mock(), Mock(),
                                patch_options=PatchOptions(**options), missions=missions)
        plan = Mock()
        plan.install.side_effect = RuntimeError('changed instructions')
        with patch('worlds.rac_size_matters.core.native_runtime.armour_pickup.prepare', return_value=plan):
            with self.assertRaisesRegex(RuntimeError, 'changed instructions'):
                runtime._prepare(7, 0xD00000)
        self.assertTrue(missions.get(Missions.CHALLAX_EXPLORE))
        self.assertEqual(missions.completed, set())

    def test_challax_opens_only_completed_doors_with_skips_disabled(self):
        row = json.loads((Path(__file__).parent / 'fixtures/shrink_ray_us.json').read_text())['Challax']
        for bits in (0, 0x10, 0x20, 0x30):
            for from_ap in (False, True):
                with self.subTest(bits=bits, from_ap=from_ap):
                    p = ShrinkMemory()
                    for address, data in row['segments']:
                        p.write_bytes(address, bytes.fromhex(data))
                    for _, rt, _ in row['locks']:
                        p.write_int32(rt + 0x4C, 0)
                        p.write_int8(rt + 0x50, 1)
                    inventory = ShrinkRaySkipInventory(p)
                    inventory.bind(7, row['base'], p.read_bytes(row['base'], 0x280000))
                    if from_ap:
                        inventory.sync_from_ap({name for name, mask in SHRINK_RAY_PUZZLE_BITS.items() if mask & bits})
                    else:
                        p.write_int16(address_maps.SHRINK_RAY_GATE_ADDRESS, bits)
                    p.writes.clear()
                    inventory.set_skip(7, False)
                    for _, rt, puzzle in row['locks']:
                        self.assertEqual(p.read_int8(rt + 0x50), int(not bits & (1 << puzzle)))
                    self.assertFalse(inventory.plan.installed)
                    self.assertEqual(p.read_int16(address_maps.SHRINK_RAY_GATE_ADDRESS), 0 if from_ap else bits)
                    self.assertTrue(all(addr in {rt + 0x50 for _, rt, _ in row['locks']} for addr, _ in p.writes))
                    p.writes.clear()
                    inventory.set_skip(7, False)
                    self.assertEqual(p.writes, [])

    def test_completed_door_waits_for_active_puzzle_to_finish(self):
        row = json.loads((Path(__file__).parent / 'fixtures/shrink_ray_us.json').read_text())['Challax']
        p = ShrinkMemory()
        for address, data in row['segments']:
            p.write_bytes(address, bytes.fromhex(data))
        inventory = ShrinkRaySkipInventory(p)
        inventory.bind(7, row['base'], p.read_bytes(row['base'], 0x280000))
        _, rt, puzzle = row['locks'][0]
        p.write_int16(address_maps.SHRINK_RAY_GATE_ADDRESS, 1 << puzzle)
        p.write_int32(rt + 0x4C, 1)
        p.write_int8(rt + 0x50, 1)
        inventory.set_skip(7, False)
        self.assertEqual(p.read_int8(rt + 0x50), 1)
        p.write_int32(rt + 0x4C, 0)
        inventory.set_skip(7, False)
        self.assertEqual(p.read_int8(rt + 0x50), 0)


class QuodronaTriggerTests(unittest.TestCase):
    fixture = json.loads((Path(__file__).parent / 'fixtures/quodrona_replay_us.json').read_text())

    def memory(self, base=0):
        p = ShrinkMemory()
        for offset, data in self.fixture['segments']:
            p.write_bytes(base + offset, bytes.fromhex(data))
        p.write_int32(base + self.fixture['init'] + 0x4C, jump(base + self.fixture['getter']))
        return p

    def test_retail_capture_has_a_walk_in_entrance_and_a_separate_exit(self):
        row = self.fixture['capture']
        entrance, exit_movie = row['movies']
        self.assertEqual(entrance['id'], 2)
        self.assertNotEqual(entrance['trigger'], 0)
        self.assertEqual(exit_movie['id'], 3)
        self.assertEqual(exit_movie['trigger'], 0)
        p = ShrinkMemory()
        for address, data in row['segments']:
            p.write_bytes(address, bytes.fromhex(data))
        plan = quodrona_replay.prepare(p, code_start=row['base'], code=p.read_bytes(row['base'], 0x280000))
        plan.install()
        plan.restore()

    def test_native_runtime_installs_quodrona_replay_before_startup(self):
        row = self.fixture['capture']
        p = ShrinkMemory()
        for address, data in row['segments']:
            p.write_bytes(address, bytes.fromhex(data))
        options = PatchOptions(**{field.name: False for field in fields(PatchOptions)})
        runtime = NativeRuntime(p, SimpleNamespace(planet=SimpleNamespace()), Mock(), Mock(),
                                patch_options=options)
        runtime._prepare(10, row['base'])
        self.assertEqual(len(runtime.plans), 1)
        self.assertTrue(runtime.plans[0].installed)
        self.assertEqual(runtime.plans[0].edits[0].address, row['init'] + 0x18)

    def test_clone_uses_walk_in_path_even_when_completed_and_preserves_other_movies(self):
        for base in (0, 0xD00000):
            p = self.memory(base)
            plan = quodrona_replay.prepare(p, code_start=base, code=p.read_bytes(base, 0x280000))
            plan.install()
            start, getter = base + self.fixture['init'], base + self.fixture['getter']
            for movie in (2, 3, 4, 5, 6):
                for completed in (False, True):
                    for check_mission in (False, True):
                        with self.subTest(base=base, movie=movie, completed=completed, check_mission=check_mission):
                            moby, properties = 0x100000, 0x100100
                            p.write_int8(moby + 0x45, movie)
                            p.write_int8(properties + 0x14, int(check_mission))
                            p.write_int8(properties + 0x15, 0)
                            p.write_int32(properties + 0x10, 6)  # Prior boss-stage progress.
                            cpu = CPU(p)
                            cpu.r[16], cpu.r[17] = properties, moby
                            reached = []

                            def query(machine):
                                self.assertEqual(machine.r[4:6], [22, movie])
                                machine.r[2] = (1 << movie) if completed else 0

                            def finish(label):
                                def stop(machine):
                                    reached.append(label)
                                    machine.r[31] = CPU.STOP
                                return stop

                            cpu.run(start + 0x18, stubs={
                                getter: query,
                                start + 0x5C: finish('stage'),
                                start + 0x98: finish('walk-in'),
                                start + 0x154: finish('disabled'),
                            })
                            expected = 'walk-in' if movie == 2 else ('disabled' if check_mission and completed else 'stage')
                            self.assertEqual(reached, [expected])
                            self.assertEqual(p.read_int8(properties + 0x15), int(movie == 2))
                            self.assertEqual(p.read_int32(properties + 0x10), 6)
            plan.restore()

    def test_changed_native_code_is_rejected_without_writes(self):
        p = self.memory()
        p.write_int32(self.fixture['init'] + 0x98, 0)
        p.writes.clear()
        with self.assertRaises(RuntimeError):
            quodrona_replay.prepare(p, code_start=0, code=p.read_bytes(0, 0x280000))
        self.assertEqual(p.writes, [])

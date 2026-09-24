import json
import struct
import unittest
from pathlib import Path
from types import SimpleNamespace

from .test_native_patches import Memory
from ..constants.shrink_ray import SHRINK_RAY_PUZZLE_BITS, SHRINK_RAY_LOCATION_PLANETS
from ..core.shrink_ray import ShrinkRaySkipInventory
from ..core.address_maps import SHRINK_RAY_GATE_ADDRESS
from ..core.patches import shrink_ray
from ..locations import SHRINK_RAY_SKIP_LOCATIONS
from ..options import ShrinkRayOptions


class ShrinkMemory(Memory):
    def read_int16(self, address):
        return struct.unpack_from('<H', self.data, address)[0]

    def write_int16(self, address, value):
        self.write_bytes(address, struct.pack('<H', value))


class TestShrinkRay(unittest.TestCase):
    def test_native_bits_and_planet_scope(self):
        names = list(SHRINK_RAY_PUZZLE_BITS)
        self.assertEqual(len(names), 10)
        for name, puzzle_id in zip(names, (0, 1, 4, 6, 7, 9, 10, 2, 5, 3)):
            with self.subTest(name=name):
                memory = ShrinkMemory()
                inventory = ShrinkRaySkipInventory(memory)
                memory.write_int16(SHRINK_RAY_GATE_ADDRESS, 1 << puzzle_id)
                memory.writes.clear()
                self.assertEqual(inventory.check(1), [])
                self.assertEqual(inventory.check(SHRINK_RAY_LOCATION_PLANETS[name]), [name])
                self.assertEqual(inventory.check(SHRINK_RAY_LOCATION_PLANETS[name]), [])
                self.assertEqual(memory.writes, [])

    def test_unrelated_challenge_is_not_completion(self):
        memory = ShrinkMemory()
        memory.write_int8(0x1F4B3EF, 1)
        inventory = ShrinkRaySkipInventory(memory)
        self.assertEqual(inventory.check(3), [])
        self.assertEqual(inventory.check(6), [])
        self.assertEqual(inventory.check(7), [])
        self.assertEqual(memory.read_int16(SHRINK_RAY_GATE_ADDRESS), 0)

    def test_all_puzzles_registered_only_in_locations_mode(self):
        class Options(SimpleNamespace):
            type_hints = {"shrink_ray_options": ShrinkRayOptions}

        self.assertEqual(set(SHRINK_RAY_SKIP_LOCATIONS), set(SHRINK_RAY_PUZZLE_BITS))
        for mode in (0, 1, 2):
            options = Options(shrink_ray_options=ShrinkRayOptions(mode))
            for location in SHRINK_RAY_SKIP_LOCATIONS.values():
                self.assertEqual(location.available(options), mode == 1)

    def test_ap_sync(self):
        memory = ShrinkMemory()
        inventory = ShrinkRaySkipInventory(memory)
        name = next(iter(SHRINK_RAY_PUZZLE_BITS))
        inventory.sync_from_ap({name, 'unrelated'})
        memory.write_int16(SHRINK_RAY_GATE_ADDRESS, 1)
        self.assertEqual(inventory.check(3), [])
        self.assertEqual(inventory.completed, {name})

    def test_retail_door_bypass_without_save_or_code_writes(self):
        fixtures = json.loads((Path(__file__).parent / 'fixtures/shrink_ray_us.json').read_text())
        for name, row in fixtures.items():
            with self.subTest(planet=name):
                memory = ShrinkMemory()
                for address, data in row['segments']:
                    memory.write_bytes(address, bytes.fromhex(data))
                for moby, rt, puzzle in row['locks']:
                    memory.write_int32(rt + 0x4C, 0)
                    memory.write_int8(rt + 0x50, 1)
                inventory = ShrinkRaySkipInventory(memory)
                base = row['base']
                inventory.bind(3, base, memory.read_bytes(base, 0x240000))
                memory.writes.clear()
                inventory.set_skip(3, False)
                inventory.set_skip(7, True)
                self.assertEqual(memory.writes, [])
                inventory.set_skip(3, True)
                self.assertEqual(len(inventory.plan.locks), len(row['locks']))
                for moby, rt, puzzle in row['locks']:
                    self.assertEqual(memory.read_int8(rt + 0x50), 0)
                count = len(memory.writes)
                inventory.set_skip(3, True)
                self.assertEqual(len(memory.writes), count)
                inventory.set_skip(3, False)
                self.assertTrue(all(address in {rt + 0x50 for _, rt, _ in row['locks']}
                                    for address, _ in memory.writes))
                for moby, rt, puzzle in row['locks']:
                    self.assertEqual(memory.read_int8(rt + 0x50), 1)
                self.assertEqual(inventory.check(3), [])
                rt = row['locks'][0][1]
                memory.write_int32(rt + 0x4C, 1)
                inventory.set_skip(3, True)
                self.assertEqual(memory.read_int8(rt + 0x50), 1)
                memory.write_int32(rt + 0x4C, 0)
                inventory.set_skip(3, True)
                self.assertEqual(memory.read_int8(rt + 0x50), 0)
                memory.write_int32(rt + 4, 0)
                memory.writes.clear()
                with self.assertRaises(RuntimeError):
                    inventory.set_skip(3, True)
                self.assertEqual(memory.writes, [])

    def test_no_lock(self):
        self.assertIsNone(shrink_ray.prepare(ShrinkMemory(), code_start=0xD00000, code=bytes(256)))

    def test_outpost_puzzle_skip_does_not_complete_location(self):
        row = json.loads((Path(__file__).parent / 'fixtures/shrink_ray_us.json').read_text())['outpost_omega']
        memory = ShrinkMemory()
        for address, data in row['segments']:
            memory.write_bytes(address, bytes.fromhex(data))
        self.assertEqual({puzzle for _, _, puzzle in row['locks']}, {2, 3})
        inventory = ShrinkRaySkipInventory(memory)
        inventory.bind(6, row['base'], memory.read_bytes(row['base'], 0x240000))
        inventory.set_skip(6, False)
        for _, rt, _ in row['locks']:
            self.assertEqual(memory.read_int8(rt + 0x50), 1)
        inventory.set_skip(6, True)
        for _, rt, _ in row['locks']:
            self.assertEqual(memory.read_int8(rt + 0x50), 0)
        self.assertEqual(memory.read_int16(SHRINK_RAY_GATE_ADDRESS), 0)
        self.assertEqual(inventory.check(6), [])
        inventory.set_skip(6, False)
        for _, rt, _ in row['locks']:
            self.assertEqual(memory.read_int8(rt + 0x50), 1)

    def test_outpost_grindrails_report_independently(self):
        memory = ShrinkMemory()
        inventory = ShrinkRaySkipInventory(memory)
        names = {int(bit): name for name, bit in SHRINK_RAY_PUZZLE_BITS.items()}
        memory.write_int16(SHRINK_RAY_GATE_ADDRESS, 0x4)
        self.assertEqual(inventory.check(6), [names[0x4]])
        memory.write_int16(SHRINK_RAY_GATE_ADDRESS, 0xC)
        self.assertEqual(inventory.check(6), [names[0x8]])
        self.assertEqual(inventory.check(6), [])
        reconnected = ShrinkRaySkipInventory(memory)
        reconnected.sync_from_ap(inventory.completed)
        self.assertEqual(reconnected.check(6), [])

"""Regional GhostLink maps must target captured player and ghost objects."""
import json
import struct
import unittest
from pathlib import Path

from ..core import address_maps
from ..core.ghost_ratchet import GhostRatchetInventory
from .test_regional_hooks import Memory


FIXTURES = json.loads((Path(__file__).parent / 'fixtures/ghost_regions.json').read_text())


class GhostRegionTests(unittest.TestCase):
    def test_regional_objects_and_follow_writes(self):
        original = address_maps.GAME_ID
        try:
            for name, fixture in FIXTURES.items():
                with self.subTest(level=name):
                    address_maps.select_game(fixture['game_id'])
                    pid = fixture['planet']
                    a = address_maps.GHOST_RATCHET_ADDRESSES[pid]
                    memory = Memory(fixture)
                    memory.write_float = lambda addr, value: memory.write_bytes(addr, struct.pack('<f', value))
                    obj = a.trigger - 0x40
                    self.assertEqual(memory.read_int32(obj + 0x24), 0x0805C334)
                    self.assertEqual(memory.read_int32(obj + 0xC), a.ghost_base - 0x14)
                    self.assertEqual(memory.read_int32(a.ghost_base + 0x2C), obj)
                    player = memory.read_int32(a.player_position + 0x10)
                    self.assertEqual(memory.read_int32(player + 0x24), 0x36919224)
                    self.assertEqual(memory.read_int32(player + 0xC), a.player_position - 0x30)
                    ghost = GhostRatchetInventory(memory)
                    self.assertEqual(ghost.read_own_position(pid), struct.unpack('<3f', memory.read_bytes(a.player_position, 12)))
                    self.assertTrue(ghost.follow(pid, 12.5, 3.0, -20.0))
                    payload = memory.read_int32(a.ghost_base + 0x44)
                    self.assertEqual(memory.writes[:2], [payload, a.trigger])
                    self.assertEqual(memory.read_int32(payload), a.player_position - 0x30)
                    self.assertEqual(memory.read_bytes(payload + 4, 0x188), bytes(0x188))
                    self.assertEqual(memory.writes[-3:], [a.ghost_base + offset for offset in (0x1C, 0x20, 0x24)])
                    self.assertEqual(struct.unpack('<3f', memory.read_bytes(a.ghost_base + 0x1C, 12)), (12.5, 3.0, -20.0))
                    ghost.stop_following()
                    self.assertEqual(memory.read_int32(a.ghost_base + 0x50), 0)
                    # A same-level reload can recycle the uninitialized payload.
                    memory.write_int32(a.ghost_base + 0x50, 0x8000)
                    memory.write_int32(payload, 0xDEADBEEF)
                    self.assertTrue(ghost.follow(pid, 1.0, 2.0, 3.0))
                    self.assertEqual(memory.read_int32(payload), a.player_position - 0x30)
                    # A changed object must fail before any ghost memory write.
                    memory.write_int32(obj + 0x24, 0)
                    memory.writes.clear()
                    self.assertFalse(ghost.follow(pid, 1.0, 2.0, 3.0))
                    self.assertEqual(memory.writes, [])
        finally:
            address_maps.select_game(original)

"""Exercise discovery with captured native objects, bound to Treehouse player slots.

The reused object excerpts are regional topology fixtures, not Treehouse captures.
"""
import struct
import unittest

from ..core import address_maps
from ..core.ghost_ratchet import GhostRatchetInventory
from ..core.patches.loader_gate import LoaderGate
from .test_ghost_regions import FIXTURES
from .test_regional_hooks import Memory


class TreehouseGhostTests(unittest.TestCase):
    def test_discovery_and_follow_validate_objects_in_each_region(self):
        original = address_maps.GAME_ID
        try:
            for game in address_maps.SUPPORTED_GAMES:
                # US and EU share object-layout addresses. US uses a captured
                # EU object fixture with the serial switched, not invented links.
                source_game = 'SCES-55019' if game == 'SCUS-97615' else game
                fixture = next(f for f in FIXTURES.values() if f['game_id'] == source_game)
                address_maps.select_game(source_game)
                expected = address_maps.GHOST_RATCHET_ADDRESSES[fixture['planet']]
                address_maps.select_game(game)
                with self.subTest(game=game):
                    memory = Memory({**fixture, 'game_id': game, 'planet': 24})
                    memory.write_float = lambda addr, value: memory.write_bytes(addr, struct.pack('<f', value))
                    gate = LoaderGate(memory, game_id=game)
                    memory.write_int32(gate.STATE, 6)
                    player = expected.player_position - 0x30
                    base = address_maps.PLANET_ADDRESSES[24].player_state - 0x100
                    memory.write_int32(base + 0x5B0, player)
                    memory.write_int32(base + 0x59C, player)
                    memory.writes.clear()
                    ghost = GhostRatchetInventory(memory)
                    found = None
                    for _ in range(192):
                        found = ghost.resolve_addresses(24)
                        if found is not None:
                            break
                    self.assertEqual(found, expected)
                    self.assertEqual(memory.writes, [])
                    self.assertTrue(ghost.follow(24, 2.0, 3.0, 4.0))
                    self.assertEqual(struct.unpack('<3f', memory.read_bytes(expected.ghost_base + 0x1C, 12)),
                                     (2.0, 3.0, 4.0))
                    # Reused addresses must not turn an uninitialized ghost
                    # visible (or clear its initialization flag on cleanup).
                    memory.write_int32(expected.ghost_base + 0x50, 0x8000)
                    memory.writes.clear()
                    ghost.stop_following()
                    self.assertEqual(memory.writes, [])
                    self.assertTrue(ghost.follow(24, 2.0, 3.0, 4.0))
                    # Loading invalidates even same-planet cached objects.
                    memory.write_int32(gate.STATE, 4)
                    memory.writes.clear()
                    ghost.stop_following()
                    self.assertFalse(ghost.follow(24, 5.0, 6.0, 7.0))
                    self.assertEqual(memory.writes, [])
                    memory.write_int32(gate.STATE, 6)
                    memory.write_int32(expected.trigger - 0x40 + 0x24, 0)
                    memory.writes.clear()
                    self.assertFalse(ghost.follow(24, 5.0, 6.0, 7.0))
                    self.assertEqual(memory.writes, [])
        finally:
            address_maps.select_game(original)

"""Treehouse bindings, checked against excerpts from each regional LEVEL_24.REL."""
import json
import struct
import unittest
from pathlib import Path
from unittest.mock import Mock

from ..constants import Rac5Gadgets, Rac5Weapons
from ..core import address_maps
from ..core.planets import PlanetInventory
from ..core.player import PlayerMovementState
from .test_runtime_refactor import Memory as ByteMemory

FIXTURES = json.loads((Path(__file__).parent / 'fixtures/treehouse_addresses.json').read_text())


class Memory(ByteMemory):
    def read_int8(self, address):
        return self.read_bytes(address & 0x1FFFFFFF, 1)[0]

    def read_int32(self, address):
        return int.from_bytes(self.read_bytes(address, 4), 'little')

    def write_int8(self, address, value):
        self.write_bytes(address, bytes([value]))

    def write_int32(self, address, value):
        self.write_bytes(address, value.to_bytes(4, 'little'))


class TreehouseAddressTests(unittest.TestCase):
    def setUp(self):
        self.original_game = address_maps.GAME_ID

    def tearDown(self):
        address_maps.select_game(self.original_game)

    def test_maps_match_regional_binary_references(self):
        for fixture in FIXTURES.values():
            with self.subTest(game=fixture['game_id']):
                address_maps.select_game(fixture['game_id'])
                mapped = address_maps.PLANET_ADDRESSES[24]
                delta = fixture['relocation_delta']
                for field, ref in fixture['references'].items():
                    code = bytes.fromhex(ref['code'])
                    high = struct.unpack_from('<I', code)[0]
                    low = struct.unpack_from('<I', code, ref['low_instruction'] * 4)[0]
                    self.assertEqual(high >> 26, 15)  # LUI
                    self.assertEqual((high >> 16) & 31, (low >> 21) & 31)
                    immediate = low & 0xFFFF
                    if immediate & 0x8000:
                        immediate -= 0x10000
                    target = ((high & 0xFFFF) << 16) + immediate + delta + ref['addend']
                    self.assertEqual(getattr(mapped, field), target, field)
                table = fixture['weapon_table']
                self.assertEqual(mapped.weapon_array,
                                 table['file_offset'] + table['inventory_offset'] + delta)

    def test_entering_treehouse_rebinds_inventory_and_leaving_unbinds_it(self):
        for fixture in FIXTURES.values():
            with self.subTest(game=fixture['game_id']):
                address_maps.select_game(fixture['game_id'])
                memory = Memory()
                planet = PlanetInventory(memory, Mock(), Mock())
                planet.set_planet(1)
                old_weapon = planet.weapons._weapon_addrs[Rac5Weapons.LACERATOR].base
                old_health = planet.player.health_addr
                planet.set_planet(24)
                planet.is_ready = True
                memory.write_int8(address_maps.CURRENT_PLANET_ADDRESS, 24)
                self.assertTrue(planet.weapons_available)
                mapped = address_maps.PLANET_ADDRESSES[24]
                self.assertEqual(planet.player.health_addr, mapped.player_state + 0x86C)
                memory.write_bytes(mapped.player_health, struct.pack('<f', 25.0))
                memory.write_bytes(mapped.max_health, struct.pack('<f', 50.0))
                memory.write_int8(mapped.player_state, PlayerMovementState.VoidDeath)
                self.assertTrue(planet.player.is_dead)
                self.assertEqual(planet.player.health, int.from_bytes(struct.pack('<f', 25.0), 'little'))
                self.assertEqual(planet.player.max_health, 50.0)
                planet.weapons.set(Rac5Weapons.LACERATOR, True)
                planet.weapons.set(Rac5Gadgets.HYPERSHOT, True)
                self.assertTrue(planet.weapons.get(Rac5Weapons.LACERATOR))
                self.assertTrue(planet.weapons.get(Rac5Gadgets.HYPERSHOT))
                self.assertEqual(memory.read_int8(old_weapon + 0x45), 0)
                self.assertEqual(memory.read_int32(old_health), 0)
                planet.weapon_cycler.applied_weapon = 3
                self.assertEqual(memory.read_int32(mapped.weapon_cycler_apply), 3)
                # An unmapped race must never retain Treehouse write targets.
                planet.set_planet(0x16)
                self.assertFalse(planet.weapons_available)
                self.assertIsNone(planet.player.health_addr)
                self.assertIsNone(planet.weapon_cycler.apply_addr)
                self.assertFalse(planet.weapons._weapon_addrs)

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


def relocated_references(fixture, delta):
    for ref in fixture['references'].values():
        words = list(struct.unpack('<' + 'I' * (len(bytes.fromhex(ref['code'])) // 4),
                                   bytes.fromhex(ref['code'])))
        low_index = ref['low_instruction']
        immediate = words[low_index] & 0xFFFF
        target = ((words[0] & 0xFFFF) << 16) + (immediate if immediate < 0x8000 else immediate - 0x10000) + delta
        words[0] = (words[0] & 0xFFFF0000) | ((target + 0x8000) >> 16)
        words[low_index] = (words[low_index] & 0xFFFF0000) | (target & 0xFFFF)
        yield delta + ref['file_offset'], struct.pack('<' + 'I' * len(words), *words)


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

    def test_relocated_treehouse_weapons_and_clank_after_travel(self):
        from ..core.no_clank import NoClank, BACKPACK_SLOTS, HIDDEN
        from ..core.patches.loader_gate import LoaderGate

        for fixture in FIXTURES.values():
            for shift in (0x1800, -0x2800):
                with self.subTest(game=fixture['game_id'], shift=shift):
                    address_maps.select_game(fixture['game_id'])
                    original = address_maps.PLANET_ADDRESSES[24]
                    delta = fixture['relocation_delta'] + shift
                    code = bytearray(0x280000)
                    for address, raw in relocated_references(fixture, delta):
                        code[address - delta:address - delta + len(raw)] = raw
                    address_maps.bind_treehouse(delta, code)
                    mapped = address_maps.PLANET_ADDRESSES[24]
                    self.assertEqual(mapped.player_state, original.player_state + shift)
                    self.assertEqual(mapped.weapon_array, original.weapon_array + shift)
                    memory = Memory()
                    memory.get_game_id = lambda: fixture['game_id']
                    memory.read_int16 = lambda address: int.from_bytes(memory.read_bytes(address, 2), 'little')
                    planet = PlanetInventory(memory, Mock(), Mock())
                    planet.set_planet(1)
                    effect = NoClank(memory)
                    # Travel loads a different overlay, with freshly allocated packs.
                    memory.write_int32(LoaderGate(memory, game_id=fixture['game_id']).STATE, 4)
                    effect.update(True)
                    planet.set_planet(24)
                    planet.is_ready = True
                    memory.write_int32(address_maps.CURRENT_PLANET_ADDRESS, 24)
                    memory.write_int32(address_maps.NEW_PLANET_START_LOAD_ADDR, 0xFFFFFFFF)
                    memory.write_int32(LoaderGate(memory, game_id=fixture['game_id']).STATE, 6)
                    base = mapped.player_state - 0x100
                    memory.write_int32(base + 0x59C, 0x200000)
                    memory.write_int32(base + 0x5B0, 0x200000)
                    for index, slot in enumerate(BACKPACK_SLOTS):
                        obj = 0x210000 + index * 0x1000
                        memory.write_int32(base + slot, obj)
                        memory.write_int32(obj + 0x40, 0x230000)
                    effect.update(True)
                    for index, slot in enumerate(BACKPACK_SLOTS):
                        self.assertEqual(memory.read_int32(base + slot), 0)
                        self.assertTrue(memory.read_int32(0x210000 + index * 0x1000 + 0x64) & HIDDEN)
                    self.assertTrue(planet.weapons_available)
                    with planet.weapons.memory():
                        planet.weapons.set(Rac5Weapons.LACERATOR, True)
                        planet.weapons.set(Rac5Gadgets.HYPERSHOT, True)
                    self.assertEqual(memory.read_int8(mapped.weapon_array + 0x45), 1)
                    self.assertEqual(memory.read_int8(original.weapon_array + 0x45), 0)
                    effect.update(False)
                    self.assertEqual(memory.read_int32(base + 0x5AC), 0x211000)

    def test_invalid_relocation_does_not_publish_addresses(self):
        fixture = FIXTURES['eu']
        address_maps.select_game(fixture['game_id'])
        original = address_maps.PLANET_ADDRESSES[24]
        delta = fixture['relocation_delta']
        code = bytearray(0x280000)
        for address, raw in relocated_references(fixture, delta):
            code[address - delta:address - delta + len(raw)] = raw
        menu = fixture['references']['menu']['file_offset']
        code[menu + 8] ^= 4
        with self.assertRaisesRegex(RuntimeError, 'disagree'):
            address_maps.bind_treehouse(delta, code)
        self.assertIs(address_maps.PLANET_ADDRESSES[24], original)
        with self.assertRaisesRegex(RuntimeError, 'one Treehouse'):
            address_maps.bind_treehouse(delta, bytes(len(code)))

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

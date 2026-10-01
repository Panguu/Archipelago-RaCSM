"""Skyboard wins and attempts are separate packed, saturating counters."""
import unittest

from ..constants import Rac5SkyboardChallenges as Races
from ..core import address_maps
from ..core.challenges import SkyboardInventory
from ..locations import ALL_LOCATIONS
from ..locations.observation import LocationObservation


class RaceMemory:
    def __init__(self):
        self.data = {}

    def read_int8(self, address):
        return self.data.get(address, 0)

    def write_int8(self, address, value):
        self.data[address] = value

    def batch_read_int8(self, addresses):
        return [self.read_int8(address) for address in addresses]


RACE_GROUPS = (
    (0x1F4B407, (Races.KALIDON_LEARNER, Races.KALIDON_TICKET, Races.KALIDON_TRICKY, Races.KALIDON_MASTER)),
    (0x1F4B409, (Races.OUTPOST_OMEGA_INTERIOR, Races.OUTPOST_OMEGA_DANGER,
                 Races.OUTPOST_OMEGA_VORTEX, Races.OUTPOST_OMEGA_VERTIGO)),
)


class TestSkyboardWins(unittest.TestCase):
    def test_attempts_never_complete_races_and_all_nonzero_win_counts_do(self):
        previous = address_maps.GAME_ID
        try:
            for serial, delta in (("SCUS-97615", 0), ("SCES-55019", 0), ("SCPS-15120", -0x1C0)):
                address_maps.select_game(serial)
                for address, names in RACE_GROUPS:
                    for index, name in enumerate(names):
                        for count in (1, 2, 3):
                            with self.subTest(serial=serial, race=name, count=count):
                                memory = RaceMemory()
                                inventory = SkyboardInventory(memory)
                                memory.data[address + delta + 1] = count << (index * 2)
                                self.assertEqual(inventory.check(), [])
                                self.assertFalse(inventory.get(name))
                                inventory.sync()
                                self.assertEqual(inventory.completed, set())
                                memory.data[address + delta] = count << (index * 2)
                                self.assertTrue(inventory.get(name))
                                self.assertEqual(inventory.check(), [name])
                                self.assertEqual(inventory.check(), [])
                                baseline = SkyboardInventory(memory)
                                baseline.sync()
                                self.assertEqual(baseline.completed, {name})
        finally:
            address_maps.select_game(previous)

    def test_catalog_decodes_each_race_independently_for_every_byte_value(self):
        for address, names in RACE_GROUPS:
            for raw in range(256):
                observation = LocationObservation(skyboard={address: raw, address + 1: 0xFF})
                for index, name in enumerate(names):
                    with self.subTest(race=name, raw=raw):
                        self.assertEqual(ALL_LOCATIONS[name].completed(observation),
                                         bool((raw >> (index * 2)) & 3))

    def test_set_and_delete_preserve_other_races_and_attempts(self):
        for address, names in RACE_GROUPS:
            for index, name in enumerate(names):
                for count in range(4):
                    with self.subTest(race=name, count=count):
                        memory = RaceMemory()
                        inventory = SkyboardInventory(memory)
                        address_live = address_maps.save_address(address)
                        shift = index * 2
                        other_races = 0xAA & ~(3 << shift)
                        memory.data[address_live] = other_races | (count << shift)
                        memory.data[address_live + 1] = 0x55
                        inventory.set(name, True)
                        self.assertEqual(memory.data[address_live], other_races | (max(count, 1) << shift))
                        inventory.delete(name)
                        self.assertEqual(memory.data[address_live], other_races)
                        self.assertEqual(memory.data[address_live + 1], 0x55)

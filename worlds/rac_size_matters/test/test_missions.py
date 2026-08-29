"""Tests for MissionInventory's planet-gating: a mission bit tied to planet X
must not be reported until the player is actually on that planet."""
import unittest

from ..constants import Rac5CutsceneLocations
from ..core.locations.mission_locations import LOCATION_TO_PLANET_ID, VALIDATED_MISSION_MAP
from ..core.missions import MissionInventory


class FakePine:
    """Minimal in-memory stand-in for Pine — MissionInventory only ever
    touches read_int16/write_int16/batch_read_int16."""

    def __init__(self) -> None:
        self.mem: dict[int, int] = {}

    def read_int16(self, address: int) -> int:
        return self.mem.get(address, 0)

    def write_int16(self, address: int, value: int) -> None:
        self.mem[address] = value

    def batch_read_int16(self, addresses: list[int]) -> list[int]:
        return [self.mem.get(address, 0) for address in addresses]


def _address_mask(name: str) -> tuple[int, int]:
    return next(key for key, loc_name in VALIDATED_MISSION_MAP.items() if loc_name == name)


class TestMissionPlanetGating(unittest.TestCase):
    def setUp(self) -> None:
        self.pine = FakePine()
        self.inventory = MissionInventory(self.pine)
        self.name = Rac5CutsceneLocations.CHALLAX_EXPLORE
        self.address, self.mask = _address_mask(self.name)
        self.owning_planet = LOCATION_TO_PLANET_ID[self.name]

    def test_bit_set_while_off_planet_is_not_reported(self) -> None:
        self.pine.mem[self.address] = self.mask
        other_planet = self.owning_planet + 1
        self.assertEqual(self.inventory.check(other_planet), [])
        self.assertNotIn(self.name, self.inventory.completed)

    def test_bit_still_fires_once_on_the_owning_planet(self) -> None:
        self.pine.mem[self.address] = self.mask
        other_planet = self.owning_planet + 1
        self.inventory.check(other_planet)  # observed while off-planet, ignored
        self.assertEqual(self.inventory.check(self.owning_planet), [self.name])
        self.assertIn(self.name, self.inventory.completed)

    def test_bit_reported_immediately_on_the_owning_planet(self) -> None:
        self.pine.mem[self.address] = self.mask
        self.assertEqual(self.inventory.check(self.owning_planet), [self.name])
        self.assertIn(self.name, self.inventory.completed)

    def test_sync_ignores_the_planet_gate(self) -> None:
        """sync() is the reconnect baseline read — it should trust whatever's
        already in memory regardless of which planet happens to be loaded."""
        self.pine.mem[self.address] = self.mask
        self.inventory.sync()
        self.assertIn(self.name, self.inventory.completed)


if __name__ == "__main__":
    unittest.main()

"""Tests for MissionInventory's planet-gating: a mission bit tied to planet X
must not be reported until the player is actually on that planet."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from ..constants import Rac5CutsceneLocations, Rac5SkyboardChallenges
from ..core.challenges import SkyboardInventory
from ..core.location_checks import LocationChecks
from ..locations import ALL_LOCATIONS
from .test_runtime_refactor import Memory
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
        self.inventory.check(other_planet)
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


class TestOutpostOmegaRematch(unittest.TestCase):
    """The skyboard rematch is completed on Outpost Omega 2 (0x17), not Outpost Omega 1 (0x06)."""

    def test_rematch_fires_on_outpost_omega_2(self) -> None:
        pine = FakePine()
        inventory = MissionInventory(pine)
        name = Rac5CutsceneLocations.OUTPOST_OMEGA_REMATCH
        address, mask = _address_mask(name)
        pine.mem[address] = mask
        self.assertEqual(inventory.check(0x17), [name])

    def test_race_completion_also_sends_rematch_without_mission_bit(self):
        for already_checked in (False, True):
            for missions_enabled in (False, True):
                with self.subTest(already_checked=already_checked, missions_enabled=missions_enabled):
                    pine = Memory()
                    race = Rac5SkyboardChallenges.OUTPOST_OMEGA_INTERIOR
                    rematch = Rac5CutsceneLocations.OUTPOST_OMEGA_REMATCH
                    completion = ALL_LOCATIONS[race].completed
                    skyboard = SkyboardInventory(pine)
                    if already_checked:
                        skyboard.sync_from_ap({race})
                    core = SimpleNamespace(
                        pine=pine, planet=SimpleNamespace(planet_id=0x17),
                        skill_points_enabled=False, clank_enabled=False, skyboard_enabled=True,
                        shrink_ray_locations_enabled=False, all_missions_enabled=missions_enabled,
                        all_cutscenes_enabled=False, missions=MissionInventory(pine), skyboard=skyboard,
                        bolts=SimpleNamespace(check=lambda _: []), send_location=Mock(),
                    )
                    checks = LocationChecks(core)
                    checks.world()
                    core.send_location.assert_not_called()
                    # Losing the race increments attempts, not wins. It must
                    # not grant the race or its fallback rematch story check.
                    pine.write_bytes(completion.key + 1, b"\x01")
                    checks.world()
                    core.send_location.assert_not_called()
                    pine.write_bytes(completion.key, bytes([completion.mask]))
                    checks.world()
                    checks.world()
                    sent = [call.args[0] for call in core.send_location.call_args_list]
                    self.assertEqual(sent.count(rematch), int(missions_enabled))
                    self.assertEqual(sent.count(race), int(not already_checked))


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import Mock

from ..constants import Rac5CutsceneLocations as Names
from ..core.core import Core
from ..core.missions import MissionInventory
from ..core.locations.mission_locations import VALIDATED_MISSION_MAP
from ..core.address_maps import CURRENT_PLANET_ADDRESS, PLANET_MISSION_ADDRESSES
from ..core.structs.game import TransitionGateStruct, TRANSITION_GATE_IDLE
from ..locations import ALL_LOCATIONS
from .test_client_gameplay import GameMemory


class TestMissionParity(unittest.TestCase):
    def setUp(self):
        self.memory = GameMemory()
        self.missions = MissionInventory(self.memory)

    def test_every_tracked_mission_waits_for_its_planet(self):
        for (address, mask), name in VALIDATED_MISSION_MAP.items():
            with self.subTest(name=name):
                memory = GameMemory()
                missions = MissionInventory(memory)
                memory.write_int16(address, mask)
                planet = ALL_LOCATIONS[name].completed.planet_id
                self.assertNotIn(name, missions.check(0))
                self.assertNotIn(name, missions.completed)
                self.assertIn(name, missions.check(planet))
                self.assertNotIn(name, missions.check(planet))

    def test_shared_word_is_read_once(self):
        address = PLANET_MISSION_ADDRESSES["Pokitaru"]
        self.memory.write_int16(address, 7)
        read = self.memory.read_int16
        self.memory.read_int16 = Mock(wraps=read)
        self.assertEqual(len(self.missions.check(1)), 3)
        self.memory.read_int16.assert_called_once_with(address)

    def test_both_outpost_overlays_share_completion(self):
        for planet in (6, 23):
            with self.subTest(planet=planet):
                missions = MissionInventory(self.memory)
                self.memory.write_int16(PLANET_MISSION_ADDRESSES["Outpost Omega"], 0x80)
                self.assertIn(Names.OUTPOST_OMEGA_ESCAPE, missions.check(planet))

    def test_checked_locations_remain_suppressed_after_planet_change(self):
        self.memory.write_int16(PLANET_MISSION_ADDRESSES["Kalidon"], 4)
        self.missions.sync_from_ap({Names.KALIDON_SEARCH})
        self.assertNotIn(Names.KALIDON_SEARCH, self.missions.check(3))

    def test_core_does_not_finish_game_from_another_planet_or_loading(self):
        core = Core(self.memory)
        core.clank_enabled = False
        core.on_goal = Mock()
        self.memory.write_int16(PLANET_MISSION_ADDRESSES["Quodrona"], 0x140)
        core.tick()
        core.on_goal.assert_not_called()
        self.memory.write_int8(CURRENT_PLANET_ADDRESS, 10)
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS, 0)
        core.tick()
        core.on_goal.assert_not_called()
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS, TRANSITION_GATE_IDLE)
        core.tick()
        core.on_goal.assert_called_once()
        core.tick()
        core.on_goal.assert_called_once()

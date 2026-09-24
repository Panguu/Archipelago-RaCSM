import unittest
from unittest.mock import Mock

from ..core.core import Core
from ..core.address_maps import CURRENT_PLANET_ADDRESS, WEAPON_ARRAY_BASE_BY_PLANET
from ..core.structs.game import TransitionGateStruct, LoadingPlanetStruct, TRANSITION_GATE_IDLE
from .test_client_gameplay import GameMemory


class TestTransitionGameplay(unittest.TestCase):
    def setUp(self):
        self.memory = GameMemory()
        self.core = Core(self.memory)
        self.core.clank_enabled = False
        self.core.tick()

    def test_destination_id_does_not_override_loading_gate(self):
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS, 0)
        self.memory.write_int32(CURRENT_PLANET_ADDRESS, 2)
        self.memory.write_int32(LoadingPlanetStruct.BASE_ADDRESS, 2)
        self.memory._write_raw = Mock(wraps=self.memory._write_raw)
        for _ in range(8):
            self.core.tick()
        self.assertFalse(self.core.planet.is_ready)
        self.assertIsNone(self.core.planet.player.health_addr)
        self.assertIsNone(self.core.planet.weapons._array_base)
        self.memory._write_raw.assert_not_called()

    def test_same_planet_reload_rebinds_and_notifies_once(self):
        ready = Mock()
        self.core.on_planet_ready = ready
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS, 0)
        self.core.tick()
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS, TRANSITION_GATE_IDLE)
        self.core.tick()
        self.core.tick()
        ready.assert_called_once()
        self.assertTrue(self.core.planet.is_ready)
        self.assertEqual(self.core.planet.weapons._array_base, WEAPON_ARRAY_BASE_BY_PLANET[1])

    def test_unknown_overlay_and_main_menu_unbind_old_addresses(self):
        for planet in (0, 0x15):
            self.memory.write_int32(CURRENT_PLANET_ADDRESS, planet)
            self.core.tick()
            self.assertFalse(self.core.planet.is_ready)
            self.assertIsNone(self.core.planet.player.health_addr)
            self.assertIsNone(self.core.planet.weapons._array_base)

    def test_departed_vendor_snapshot_is_not_restored_into_next_overlay(self):
        self.core.vendor._level_snapshot = {"lacerator": 7}
        self.core.vendor._weapon_vendor_open = True
        self.core.weapon_vendor.activate()
        self.core.planet.weapons.restore_levels = Mock()
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS, 0)
        self.core.tick()
        self.memory.write_int32(CURRENT_PLANET_ADDRESS, 2)
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS, TRANSITION_GATE_IDLE)
        self.core.tick()
        self.assertFalse(self.core.vendor_active)
        self.assertEqual(self.core.vendor._level_snapshot, {})
        self.core.planet.weapons.restore_levels.assert_not_called()

    def test_pickup_snapshot_does_not_survive_departure(self):
        self.core.planet._was_picking_up = True
        self.core.planet._equipped_pickup_baseline = {"helmet": 7}
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS, 0)
        self.core.tick()
        self.assertFalse(self.core.planet._was_picking_up)
        self.assertIsNone(self.core.planet._equipped_pickup_baseline)

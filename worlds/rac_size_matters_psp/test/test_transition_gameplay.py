import unittest
from unittest.mock import Mock

from ..core.core import Core
from ..constants import Rac5Locations
from ..core.weapons import WeaponInventory
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

    def test_quodrona_loaded_gadgets_do_not_send_other_planets_pickups(self):
        sent = Mock()
        self.core.send_location = sent
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS, 0)
        self.core.tick()
        destination = WeaponInventory(self.memory)
        destination.set_base(WEAPON_ARRAY_BASE_BY_PLANET[10])
        destination.set("shrink_ray", True)
        destination.set("sprout_o_matic", True)
        self.memory.write_int32(CURRENT_PLANET_ADDRESS, 10)
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS, TRANSITION_GATE_IDLE)
        self.core.tick()
        self.assertNotIn(unittest.mock.call(Rac5Locations.KALIDON_SHRINK), sent.call_args_list)
        self.assertNotIn(unittest.mock.call(Rac5Locations.RYLLUS_SPROUT), sent.call_args_list)

    def test_gadget_detection_and_resync_require_pickup_planet(self):
        for name, planet, location in (
            ("shrink_ray", 3, Rac5Locations.KALIDON_SHRINK),
            ("sprout_o_matic", 2, Rac5Locations.RYLLUS_SPROUT),
        ):
            for current_planet in (10, planet):
                for resync in (False, True):
                    with self.subTest(name=name, planet=current_planet, resync=resync):
                        self.memory.write_int32(CURRENT_PLANET_ADDRESS, current_planet)
                        self.core.tick()
                        wi = self.core.planet.weapons
                        wi.set(name, False)
                        wi.sync_slots()
                        sent = Mock()
                        self.core.send_location = sent
                        wi.set(name, True)
                        if resync:
                            wi.sync_slots()
                            self.core._sync_weapon_gadget_ownership()
                        else:
                            self.core._check_vendor_purchases()
                        self.assertEqual(
                            unittest.mock.call(location) in sent.call_args_list,
                            current_planet == planet,
                        )

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

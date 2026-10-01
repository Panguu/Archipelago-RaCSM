import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from ..client.pine_mixin import PineMixin
from ..constants import Rac5WeaponKeys
from ..core.save_data import highest_weapon_levels
from ..core.planets import PlanetInventory
from ..core.weapons import PROGRESSIVE_AUTOMATIC, PROGRESSIVE_MANUAL, WeaponInventory
from ..data.weapons import WEAPON_MAX_LEVELS
from .test_runtime_refactor import Memory

LACERATOR = Rac5WeaponKeys.LACERATOR
SCORCHER = Rac5WeaponKeys.SCORCHER


def _inventory() -> WeaponInventory:
    inventory = WeaponInventory(Memory())
    inventory.set_base(0x1000)
    return inventory


class TestHighestWeaponLevels(unittest.TestCase):
    def test_keeps_highest_level_per_weapon(self):
        self.assertEqual(
            highest_weapon_levels({LACERATOR: 3, SCORCHER: 1}, {LACERATOR: 0, SCORCHER: 2}),
            {LACERATOR: 3, SCORCHER: 2},
        )

    def test_ignores_invalid_readings(self):
        too_high = WEAPON_MAX_LEVELS[LACERATOR]
        self.assertEqual(
            highest_weapon_levels({LACERATOR: 1}, {LACERATOR: too_high, SCORCHER: -1, "not_a_weapon": 2}),
            {LACERATOR: 1},
        )


class TestLevelCeilings(unittest.TestCase):
    def test_no_ceiling_without_progressive_or_challenge_mode(self):
        inventory = _inventory()
        self.assertEqual(inventory.within_level_ceilings({LACERATOR: 3}), {LACERATOR: 3})

    def test_automatic_mode_caps_to_received_copies(self):
        inventory = _inventory()
        inventory.progressive_mode = PROGRESSIVE_AUTOMATIC
        inventory.level_caps[LACERATOR] = 1
        self.assertEqual(inventory.within_level_ceilings({LACERATOR: 3}), {LACERATOR: 1})

    def test_manual_mode_caps_to_received_copies(self):
        inventory = _inventory()
        inventory.progressive_mode = PROGRESSIVE_MANUAL
        inventory.level_caps[LACERATOR] = 2
        self.assertEqual(inventory.within_level_ceilings({LACERATOR: 3}), {LACERATOR: 2})


class TestManualBoostedProgression(unittest.TestCase):
    def test_large_boost_only_awards_next_permitted_level(self):
        for cap in (1, 2, 3):
            with self.subTest(cap=cap):
                inventory = _inventory()
                inventory.progressive_mode = PROGRESSIVE_MANUAL
                inventory.experience_multiplier = 16
                inventory.level_caps[LACERATOR] = cap
                addr = inventory._weapon_addrs[LACERATOR]
                addr.unlocked = True
                inventory.check()
                inventory.update_progression()
                addr.experience = 2000
                inventory.update_progression()
                self.assertEqual((addr.level, addr.experience), (1, 0))
                self.assertEqual(inventory._prev_experience[LACERATOR], 0)
                self.assertEqual(inventory.check()["levels"], [(LACERATOR, 2)])
                inventory.update_progression()
                self.assertEqual((addr.level, addr.experience), (1, 0))
                self.assertEqual(inventory.check()["levels"], [])

    def test_cap_holds_until_next_copy_then_new_xp_can_level(self):
        inventory = _inventory()
        inventory.progressive_mode = PROGRESSIVE_MANUAL
        inventory.experience_multiplier = 16
        inventory.level_caps[LACERATOR] = 1
        addr = inventory._weapon_addrs[LACERATOR]
        addr.unlocked = True
        addr.level = 1
        inventory.update_progression()
        addr.experience = 2000
        inventory.update_progression()
        self.assertEqual((addr.level, addr.experience), (1, 0))
        inventory.level_caps[LACERATOR] = 2
        inventory.update_progression()
        self.assertEqual((addr.level, addr.experience), (1, 0))
        addr.experience = 600
        inventory.update_progression()
        self.assertEqual((addr.level, addr.experience), (2, 0))

    def test_partial_boost_remains_available_for_next_gain(self):
        inventory = _inventory()
        inventory.progressive_mode = PROGRESSIVE_MANUAL
        inventory.experience_multiplier = 16
        inventory.level_caps[LACERATOR] = 1
        addr = inventory._weapon_addrs[LACERATOR]
        inventory.update_progression()
        addr.experience = 100
        inventory.update_progression()
        self.assertEqual((addr.level, addr.experience), (0, 1600))
        addr.experience += 100
        inventory.update_progression()
        self.assertEqual((addr.level, addr.experience), (1, 0))


class TestPersistGuard(unittest.TestCase):
    def _client(self, inventory, known):
        weapons = inventory
        return SimpleNamespace(
            slot=1, pine_connected=True, _weapon_state_restored=True, _save_data_received=True,
            _items_received_ready=True, _local_weapon_state=dict(known), _pushed_weapon_state=dict(known),
            _last_weapon_state_push=time.monotonic(),
            _wiring=SimpleNamespace(
                planet=SimpleNamespace(is_ready=True, weapons_available=True, weapons=weapons), at_main_menu=False,
                vendor_active=False, native=SimpleNamespace(waiting=False),
            ),
        )

    def test_dropped_level_is_repaired_not_saved(self):
        inventory = _inventory()
        inventory._weapon_addrs[LACERATOR].level = 0
        client = self._client(inventory, {LACERATOR: 3})
        with self.assertLogs("Client", level="WARNING"):
            PineMixin._maybe_persist_weapon_state(client)
        self.assertEqual(client._local_weapon_state[LACERATOR], 3)
        self.assertEqual(inventory._weapon_addrs[LACERATOR].level, 3)

    def test_level_up_is_kept(self):
        inventory = _inventory()
        inventory._weapon_addrs[LACERATOR].level = 3
        client = self._client(inventory, {LACERATOR: 2})
        PineMixin._maybe_persist_weapon_state(client)
        self.assertEqual(client._local_weapon_state[LACERATOR], 3)

    def test_progressive_cap_is_not_fought(self):
        inventory = _inventory()
        inventory.progressive_mode = PROGRESSIVE_AUTOMATIC
        inventory.level_caps[LACERATOR] = 1
        inventory._weapon_addrs[LACERATOR].level = 1
        client = self._client(inventory, {LACERATOR: 3})
        PineMixin._maybe_persist_weapon_state(client)
        self.assertEqual(client._local_weapon_state[LACERATOR], 1)
        self.assertEqual(inventory._weapon_addrs[LACERATOR].level, 1)

    def test_race_does_not_repair_or_publish_missing_weapon_levels(self):
        inventory = _inventory()
        inventory.set_base(None)
        client = self._client(inventory, {LACERATOR: 3})
        client._wiring.planet.weapons_available = False
        client._persist_weapon_state = Mock()
        with self.assertNoLogs("Client", level="WARNING"):
            for _ in range(3):
                PineMixin._maybe_persist_weapon_state(client, force=True)
        self.assertEqual(client._local_weapon_state, {LACERATOR: 3})
        client._persist_weapon_state.assert_not_called()


class TestRaceWeaponAvailability(unittest.TestCase):
    def test_no_weapon_access_during_race_or_before_transition_is_observed(self):
        for planet_id, live_id, ready, expected in (
            (3, 3, True, True),
            (3, 0x16, True, False),
            (0x16, 0x16, True, False),
            (0x16, 3, True, False),
            (3, 3, False, False),
        ):
            with self.subTest(planet_id=planet_id, live_id=live_id, ready=ready):
                planet = SimpleNamespace(
                    planet_id=planet_id, is_ready=ready, giant_clank_active=False,
                    pine=SimpleNamespace(read_int8=lambda _: live_id),
                )
                self.assertEqual(PlanetInventory.weapons_available.fget(planet), expected)

    def test_race_return_keeps_game_restored_level_and_experience(self):
        inventory = _inventory()
        addr = inventory._weapon_addrs[LACERATOR]
        addr.unlocked = True
        addr.level = 2
        addr.experience = 1234
        inventory.wipe(preserve_levels=True)
        self.assertEqual(addr.level, 2)
        self.assertEqual(addr.experience, 1234)
        self.assertEqual(inventory._prev_experience[LACERATOR], 1234)
        inventory.set(LACERATOR, True)
        self.assertEqual(inventory.check()["levels"], [])

import time
import unittest
from types import SimpleNamespace

from ..client.pine_mixin import PineMixin
from ..constants import Rac5WeaponKeys
from ..core.save_data import highest_weapon_levels
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


class TestPersistGuard(unittest.TestCase):
    def _client(self, inventory, known):
        weapons = inventory
        return SimpleNamespace(
            slot=1, pine_connected=True, _weapon_state_restored=True, _save_data_received=True,
            _items_received_ready=True, _local_weapon_state=dict(known), _pushed_weapon_state=dict(known),
            _last_weapon_state_push=time.monotonic(),
            _wiring=SimpleNamespace(
                planet=SimpleNamespace(is_ready=True, weapons=weapons), at_main_menu=False,
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

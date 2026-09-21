import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from ..client.context import RACContext
from ..core.armour import ArmourInventory, ArmourPiece, ArmourSnapshot
from ..core.core import Core
from ..core.save_data import RAC5SaveData
from ..core.weapons import WeaponInventory


def context():
    ctx = RACContext.__new__(RACContext)
    ctx.slot, ctx.team = 1, 0
    ctx.pine_connected = True
    ctx._save_data_received = False
    ctx._items_received_ready = True
    ctx._weapon_state_restored = False
    ctx._local_weapon_state = {}
    ctx._pushed_weapon_state = {}
    ctx._last_weapon_state_push = 0.0
    ctx.stored_data = {ctx._save_data_key(): {"weapon_state": {"lacerator": 2}}}
    ctx._wiring = SimpleNamespace(
        planet=SimpleNamespace(is_ready=True, weapons=Mock()),
        at_main_menu=False, vendor_active=False, native=SimpleNamespace(waiting=False))
    ctx.send_msgs = AsyncMock()
    return ctx


class ReconnectStateTests(unittest.TestCase):
    def test_restore_waits_for_fresh_storage_reply(self):
        ctx = context()
        ctx._try_restore_weapon_state(force=True)
        self.assertFalse(ctx._weapon_state_restored)
        ctx._wiring.planet.weapons.restore_levels.assert_not_called()
        ctx._save_data_received = True
        ctx._try_restore_weapon_state()
        ctx._wiring.planet.weapons.restore_levels.assert_called_once_with({"lacerator": 2})
        self.assertEqual(ctx._local_weapon_state, {"lacerator": 2})

    def test_planet_restore_uses_newer_local_levels(self):
        ctx = context()
        ctx._save_data_received = True
        ctx._weapon_state_restored = True
        ctx._local_weapon_state = {"lacerator": 3}
        ctx._try_restore_weapon_state(force=True)
        ctx._wiring.planet.weapons.restore_levels.assert_called_once_with({"lacerator": 3})

    def test_old_save_migrates_levels_and_discards_experience(self):
        data = RAC5SaveData.from_dict({"weapon_state": {
            "lacerator": [3, 12345], "ryno": 99, "unknown": 2, "scorcher": "bad"}})
        self.assertEqual(data.to_dict()["weapon_state"], {"lacerator": 3})

    def test_wipe_restore_leaves_experience_and_rebaselines_levels(self):
        wi = WeaponInventory.__new__(WeaponInventory)
        addr = SimpleNamespace(unlocked=True, level=3, experience=12345,
                               mod_slot_one=True, mod_slot_two=False, mod_slot_three=False)
        wi._weapon_addrs = {"lacerator": addr}
        wi._gadget_addrs = {}
        snapshot = wi.level_snapshot()
        wi.wipe()
        wi.restore_levels(snapshot)
        self.assertEqual((addr.level, addr.experience), (3, 12345))
        self.assertEqual(wi._raw_level, snapshot)

    def test_planet_ap_grants_rebaseline_pickup_detection(self):
        core = Core.__new__(Core)
        wi = WeaponInventory.__new__(WeaponInventory)
        wi._weapon_addrs = {"lacerator": SimpleNamespace(unlocked=False)}
        wi._gadget_addrs = {"hypershot": SimpleNamespace(unlocked=False)}
        wi.weapons, wi.gadgets = {}, {}
        wi._raw_weapons, wi._raw_gadgets = {}, {}
        core.planet = SimpleNamespace(weapons=wi)
        core._ap_owned_weapons = {"lacerator": True}
        core._ap_owned_gadgets = {"hypershot": True}
        core.send_location = Mock()
        core._sync_weapon_gadget_ownership()
        self.assertTrue(wi._raw_weapons["lacerator"])
        self.assertTrue(wi._raw_gadgets["hypershot"])
        core.send_location.assert_not_called()

    def test_armour_detection_waits_for_ap_inventory(self):
        core = Core.__new__(Core)
        core._ap_inventory_ready = False
        core.armour = ArmourInventory(Mock())
        core.armour.read = Mock(return_value=ArmourSnapshot(wildfire=ArmourPiece.CHESTPLATE))
        core.send_location = Mock()
        core._report_new_armour_pickups()
        core.armour.read.assert_not_called()
        core.armour.set_ap_armour({"wildfire": int(ArmourPiece.CHESTPLATE)})
        core._ap_inventory_ready = True
        core._report_new_armour_pickups()
        core.send_location.assert_not_called()


class PersistLevelTests(unittest.IsolatedAsyncioTestCase):
    async def test_level_up_sends_only_levels_immediately(self):
        ctx = context()
        ctx._save_data_received = ctx._weapon_state_restored = True
        ctx._last_weapon_state_push = float("inf")
        ctx._wiring.planet.weapons.level_snapshot.return_value = {"lacerator": 3}
        ctx._on_weapon_level_up()
        await asyncio.sleep(0)
        packet = ctx.send_msgs.call_args.args[0][0]
        self.assertEqual(packet["operations"], [{"operation": "update", "value": {
            "weapon_state": {"lacerator": 3}}}])
        self.assertEqual(ctx._local_weapon_state, {"lacerator": 3})

    async def test_no_publish_before_restore_or_during_vendor(self):
        ctx = context()
        ctx._maybe_persist_weapon_state(force=True)
        ctx._save_data_received = ctx._weapon_state_restored = True
        ctx._wiring.vendor_active = True
        ctx._maybe_persist_weapon_state(force=True)
        await asyncio.sleep(0)
        ctx.send_msgs.assert_not_called()
        ctx._wiring.planet.weapons.level_snapshot.assert_not_called()

    async def test_force_sync_restores_even_if_already_restored(self):
        ctx = context()
        ctx._save_data_received = ctx._weapon_state_restored = True
        ctx._local_weapon_state = {"lacerator": 3}
        ctx._pine_lock = asyncio.Lock()
        ctx._parse_inventory = Mock(return_value={})
        ctx._checked_location_names = Mock(return_value=set())
        ctx._wiring.apply_inventory = Mock()
        ctx._wiring.restore_world_states = Mock()
        ctx._wiring.restore_armour_from_locations = Mock()
        await ctx.force_sync()
        ctx._wiring.planet.weapons.wipe.assert_called_once()
        ctx._wiring.planet.weapons.restore_levels.assert_called_once_with({"lacerator": 3})

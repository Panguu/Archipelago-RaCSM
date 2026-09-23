import asyncio
import unittest
from unittest.mock import AsyncMock, Mock

from ..client.psp_mixin import PspMixin
from ..client.server_sync import ServerSyncMixin
from ..core.address_maps import PLAYER_BOLT_COUNT
from ..core.structs.game import TransitionGateStruct
from .test_client_gameplay import ClientHarness, item


class SyncHarness(ClientHarness):
    def __init__(self):
        super().__init__()
        self._reset_server_sync()
        self.stored_data = {}
        self._starting_skin_option = 0
        self._try_restore_weapon_state = Mock()

    def _qs_storage_key(self):
        return "quickselect"

    def _armour_slots_storage_key(self):
        return "armour"

    def _starting_items_key(self):
        return "starting"

    def _weapon_state_storage_key(self):
        return "weapons"

    def retrieve(self, checkpoint=0, keys=None):
        values = {key: None for key in self._server_storage_keys()}
        values[self._filler_applied_key()] = checkpoint
        if keys is not None:
            values = {key: values[key] for key in keys}
        self.stored_data.update(values)
        self._record_server_snapshot("Retrieved", {"keys": values})

    def receipts(self, count, index=0):
        self.items_received = [item(2)] * count
        self._record_server_snapshot("ReceivedItems", {"index": index})


class TestServerSync(unittest.IsolatedAsyncioTestCase):
    async def test_storage_before_items_does_not_replay_old_rewards(self):
        ctx = SyncHarness()
        ctx.retrieve(checkpoint=2)
        await ctx._apply_received_items()
        self.assertFalse(ctx._filler_checkpoint_synced)
        ctx.receipts(3)
        await ctx._apply_received_items()
        self.assertEqual(ctx.pine.read_int32(PLAYER_BOLT_COUNT), 75000 + 45000)
        self.assertEqual(ctx._processed_item_count, 3)
        await ctx._apply_received_items()
        self.assertEqual(ctx.pine.read_int32(PLAYER_BOLT_COUNT), 120000)

    async def test_items_before_storage_leave_game_untouched(self):
        ctx = SyncHarness()
        ctx.receipts(3)
        before = bytes(ctx.pine.data)
        await ctx._apply_received_items()
        await ctx.force_sync()
        await PspMixin._poll_game(ctx)
        PspMixin._read_initial_state_sync(ctx)
        self.assertEqual(bytes(ctx.pine.data), before)
        ctx.retrieve(checkpoint=3)
        self.assertTrue(ctx._server_state_ready)
        self.assertEqual(ctx._processed_item_count, 3)

    async def test_stale_cache_and_unrelated_reply_do_not_unlock_sync(self):
        ctx = SyncHarness()
        ctx.stored_data = dict.fromkeys(ctx._server_storage_keys(), {})
        ctx.receipts(1, index=1)
        ctx._record_server_snapshot("SetReply", {"key": "unrelated", "value": 1})
        ctx.retrieve(keys={ctx._filler_applied_key()})
        self.assertFalse(ctx._server_state_ready)
        ctx.retrieve()
        self.assertFalse(ctx._server_state_ready)
        ctx.receipts(0)
        self.assertTrue(ctx._server_state_ready)

    async def test_partial_storage_replies_accumulate(self):
        ctx = SyncHarness()
        ctx.receipts(0)
        for key in ctx._server_storage_keys():
            ctx.retrieve(keys={key})
        self.assertTrue(ctx._server_state_ready)

    async def test_disconnect_requires_fresh_snapshots(self):
        ctx = SyncHarness()
        ctx.retrieve(1)
        ctx.receipts(1)
        ctx._starting_items_sent = True
        ctx._reset_server_sync()
        self.assertFalse(ctx._server_state_ready)
        self.assertFalse(ctx._starting_items_sent)
        before = bytes(ctx.pine.data)
        await ctx._apply_received_items()
        self.assertEqual(bytes(ctx.pine.data), before)

    async def test_loadout_waits_for_gameplay_and_vendor_close(self):
        ctx = SyncHarness()
        ctx.retrieve()
        ctx.receipts(0)
        ctx.stored_data[ctx._qs_storage_key()] = {"test": 1}
        ctx._wiring.quick_select.load = Mock()
        ctx._wiring.quick_select.restore = Mock()
        ctx._wiring.planet.is_ready = False
        ServerSyncMixin._restore_server_loadout(ctx)
        self.assertFalse(ctx._ap_loadout_restored)
        ctx._wiring.planet.is_ready = True
        ctx._wiring.weapon_vendor.active = True
        ServerSyncMixin._restore_server_loadout(ctx)
        self.assertFalse(ctx._ap_loadout_restored)
        ctx._wiring.weapon_vendor.active = False
        ServerSyncMixin._restore_server_loadout(ctx)
        self.assertTrue(ctx._ap_loadout_restored)
        ctx._wiring.quick_select.load.assert_called_once_with({"test": 1})
        ServerSyncMixin._restore_server_loadout(ctx)
        ctx._wiring.quick_select.restore.assert_called_once()

    async def test_raw_transition_blocks_receipt_writes_before_next_poll(self):
        ctx = SyncHarness()
        ctx.retrieve()
        ctx.receipts(1)
        ctx.pine.write_int32(TransitionGateStruct.BASE_ADDRESS, 0)
        before = bytes(ctx.pine.data)
        await ctx._apply_received_items()
        self.assertEqual(bytes(ctx.pine.data), before)
        self.assertEqual(ctx._processed_item_count, 0)

    async def test_real_context_restores_inventory_loadout_and_xp_after_handshake(self):
        from ..client.context import RACContext
        from ..core.core import Core
        from ..core.structs.game import QuickSelectStruct
        from .test_client_gameplay import GameMemory

        ctx = RACContext(None, None)
        ctx.keep_alive_task.cancel()
        await asyncio.gather(ctx.keep_alive_task, return_exceptions=True)
        ctx.pine = ctx.memory = GameMemory()
        ctx._wiring = Core(ctx.pine)
        ctx.native = Mock()
        ctx.psp_connected = True
        ctx.slot, ctx.team = 1, 0
        ctx.send_msgs = AsyncMock()
        ctx._send_map_page = AsyncMock()
        ctx.item_names = {ctx.game: {1: "Lacerator", 2: "Bolts"}}
        ctx._show_new_item_notifications = Mock()
        ctx.on_package("Connected", {"slot_data": {"split_infobots": True, "clank_challenges": 0}})
        await asyncio.sleep(0)
        before = bytes(ctx.pine.data)
        await ctx._poll_game()
        self.assertEqual(bytes(ctx.pine.data), before)

        saved = dict.fromkeys(ctx._server_storage_keys(), None)
        saved[ctx._filler_applied_key()] = 2
        saved[ctx._weapon_state_storage_key()] = {"lacerator": [2, 1234]}
        saved[ctx._qs_storage_key()] = {"right": 2}
        ctx.stored_data.update(saved)
        ctx.on_package("Retrieved", {"keys": saved})
        await asyncio.sleep(0)
        self.assertEqual(bytes(ctx.pine.data), before)
        ctx.items_received = [item(1), item(2)]
        ctx.on_package("ReceivedItems", {"index": 0})
        await asyncio.sleep(0)
        await ctx._poll_game()
        await asyncio.sleep(0)
        self.assertTrue(ctx._wiring.planet.weapons.get("lacerator"))
        self.assertEqual(ctx._wiring.planet.weapons.level_experience_snapshot()["lacerator"], [2, 1234])
        self.assertEqual(ctx.pine.read_int32(QuickSelectStruct.BASE_ADDRESS), 2)
        self.assertEqual(ctx.pine.read_int32(PLAYER_BOLT_COUNT), 0)
        self.assertTrue(ctx._weapon_state_restored)
        self.assertTrue(ctx._ap_loadout_restored)
        await ctx.force_sync()
        self.assertEqual(ctx._wiring.planet.weapons.level_experience_snapshot()["lacerator"], [2, 1234])

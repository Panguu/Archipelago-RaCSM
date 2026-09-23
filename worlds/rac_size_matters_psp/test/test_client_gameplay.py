import asyncio
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock

from ..client.handlers import EventsHandlerMixin
from ..client.vendor import InventoryMixin
from ..client.server_sync import ServerSyncMixin
from ..core.core import Core
from ..core.address_maps import CURRENT_PLANET_ADDRESS, PLAYER_BOLT_COUNT
from ..core.structs.game import TransitionGateStruct, TRANSITION_GATE_IDLE
from ..procmem.transport import ProcMemTransport


class GameMemory(ProcMemTransport):
    """Synthetic guest RAM: exercise real accessors without a running emulator."""
    def __init__(self):
        self.data = bytearray(0x2000000)
        self.write_int32(CURRENT_PLANET_ADDRESS, 1)
        self.write_int32(TransitionGateStruct.BASE_ADDRESS, TRANSITION_GATE_IDLE)

    def _read_raw(self, address, size):
        if not 0x08000000 <= address <= address + size <= 0x0a000000:
            raise ValueError("outside PSP RAM")
        return bytes(self.data[address - 0x08000000:address - 0x08000000 + size])

    def _write_raw(self, address, data):
        self._read_raw(address, len(data))
        offset = address - 0x08000000
        self.data[offset:offset + len(data)] = data

    def validate_session(self):
        pass


class ClientHarness(ServerSyncMixin, InventoryMixin, EventsHandlerMixin):
    def __init__(self):
        self.pine = GameMemory()
        self._wiring = Core(self.pine)
        self._wiring.clank_enabled = False
        self._wiring.tick()
        self.psp_connected = True
        self.game = "PSP"
        self.items_received = []
        self.item_names = {"PSP": {1: "Lacerator", 2: "Bolts", 3: "Hypershot"}}
        self.slot_data = {"starting_bolts": 45000}
        self._psp_lock = asyncio.Lock()
        self._processed_item_count = self._processed_trap_count = 0
        self._filler_checkpoint_synced = True
        self._starting_checkpoint_synced = False
        self._starting_items_sent = False
        self._notification_item_index = 0
        self._pending_item_apply = True
        self._items_received_ready = self._save_data_received = True
        self._restore_server_loadout = Mock()
        self.send_msgs = AsyncMock()
        self._persist_starting_items_sent = AsyncMock()
        self._show_new_item_notifications = Mock()

    def _filler_applied_key(self):
        return "test_filler"


def item(code, location=100):
    return SimpleNamespace(item=code, location=location)


class TestClientGameplay(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.ctx = ClientHarness()

    async def test_standard_client_help_does_not_require_tracker_context(self):
        from ..client.command_processor import RACCommandProcessor
        help_text = RACCommandProcessor(SimpleNamespace()).get_help_text()
        self.assertIn("reconnect", help_text)

    async def test_receipts_apply_through_real_core_without_false_pickups(self):
        ctx = self.ctx
        ctx.items_received = [item(1, -2), item(3, -2)]
        checked = Mock()
        ctx._wiring.send_location = checked
        await ctx._apply_received_items()
        self.assertTrue(ctx._wiring.planet.weapons.get("lacerator"))
        self.assertTrue(ctx._wiring.planet.weapons.get("hypershot"))
        for _ in range(3):
            ctx._wiring.tick()
            await ctx._apply_received_items()
        checked.assert_not_called()

    async def test_loading_does_not_consume_filler(self):
        ctx = self.ctx
        ctx.items_received = [item(2)]
        ctx._wiring.planet.is_ready = False
        await ctx._apply_received_items()
        self.assertEqual(ctx._processed_item_count, 0)
        self.assertEqual(ctx.pine.read_int32(PLAYER_BOLT_COUNT), 0)
        ctx._wiring.planet.is_ready = True
        await ctx._apply_received_items()
        self.assertEqual(ctx.pine.read_int32(PLAYER_BOLT_COUNT), 75000)
        await ctx._apply_received_items()
        self.assertEqual(ctx.pine.read_int32(PLAYER_BOLT_COUNT), 75000)

    async def test_starting_grant_waits_for_checkpoint_and_loaded_game(self):
        ctx = self.ctx
        await ctx._grant_starting_items()
        self.assertFalse(ctx._starting_items_sent)
        ctx._starting_checkpoint_synced = True
        ctx._wiring.planet.is_ready = False
        await ctx._grant_starting_items()
        self.assertFalse(ctx._starting_items_sent)
        ctx._wiring.planet.is_ready = True
        await asyncio.gather(ctx._grant_starting_items(), ctx._grant_starting_items())
        self.assertEqual(ctx.pine.read_int32(PLAYER_BOLT_COUNT), 45000)

    async def test_only_precollected_starting_placeholder_is_skipped(self):
        ctx = self.ctx
        ctx.items_received = [item(2, 123), item(2, -2), item(2, 456)]
        await ctx._apply_received_items()
        self.assertEqual(ctx.pine.read_int32(PLAYER_BOLT_COUNT), 150000)
        self.assertEqual(ctx._processed_item_count, 3)

    async def test_failed_reward_stays_pending(self):
        ctx = self.ctx
        ctx.items_received = [item(1), item(2)]
        write = ctx.pine.write_int32
        def fail_bolts(address, value):
            if address == PLAYER_BOLT_COUNT:
                raise OSError("lost write")
            write(address, value)
        ctx.pine.write_int32 = fail_bolts
        with self.assertRaises(OSError):
            await ctx._apply_received_items()
        self.assertEqual(ctx._processed_item_count, 1)
        self.assertEqual(ctx.send_msgs.call_args.args[0][0]["operations"][0]["value"], 1)
        ctx.pine.write_int32 = write
        await ctx._apply_received_items()
        self.assertEqual(ctx.pine.read_int32(PLAYER_BOLT_COUNT), 75000)

    async def test_formerly_preset_missions_are_reported_once(self):
        from ..core.locations.mission_locations import VALIDATED_MISSION_MAP
        names = {"Pokitaru: Rescue the girl", "Kalidon: Search the factory",
                 "Challax: Explore the miniature city"}
        for (address, mask), name in VALIDATED_MISSION_MAP.items():
            if name in names:
                self.ctx.pine.write_int16(address, self.ctx.pine.read_int16(address) | mask)
        reported = set()
        for planet_id in (1, 3, 7):
            reported.update(self.ctx._wiring.missions.check(planet_id))
        self.assertEqual(reported, names)
        self.assertEqual(self.ctx._wiring.missions.check(), [])

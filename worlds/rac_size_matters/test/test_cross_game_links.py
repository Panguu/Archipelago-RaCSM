import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from ..client.ring_link import RingLinkMixin
from ..client.trap_link import TrapLinkMixin, TRAP_LINK_NAMES
from ..constants import Rac5Traps
from ..core.player_bolts import PlayerBoltInventory, MAX_PLAYER_BOLTS


class BoltMemory:
    value = 1000

    def read_int32(self, address):
        return self.value

    def write_int32(self, address, value):
        self.value = value


class LinkContext(RingLinkMixin, TrapLinkMixin):
    def __init__(self):
        self.pine = BoltMemory()
        self.slot = 1
        self.auth = 'Ratchet'
        self.ap_connected = self.pine_connected = True
        self._items_received_ready = self._save_data_received = True
        self._connection_sync_pending = False
        self._ring_link_enabled = self._trap_link_enabled = True
        self._trap_link_seen = set()
        self.slot_data = {}
        self._pine_lock = asyncio.Lock()
        self._wiring = SimpleNamespace(
            player_bolts=PlayerBoltInventory(self.pine), at_main_menu=False,
            planet=SimpleNamespace(is_ready=True, weapons=Mock()), native=SimpleNamespace(waiting=False))
        self._wiring.player_bolts.multiplier = 4
        self._wiring.player_bolts.on_change = self._record_ring_link_change
        self._wiring.player_bolts.rebaseline()
        self._reset_ring_link()
        self._log = Mock()
        self.send_msgs = AsyncMock()
        self._update_link_tag = AsyncMock()


class RingLinkTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ready = patch('worlds.rac_size_matters.client.ring_link.traps_ready', return_value=True)
        self.ready.start()
        self.addCleanup(self.ready.stop)
        self.ctx = LinkContext()

    async def flush(self):
        self.ctx._last_ring_link_push = 0
        self.ctx._maybe_sync_ring_link()
        await asyncio.sleep(0)

    async def test_multiplier_and_fractional_pickups(self):
        c = self.ctx
        for multiplier in (0, 1, 4, 16):
            c._wiring.player_bolts.multiplier = multiplier
            c._ring_link_remainder = 0
            c.send_msgs.reset_mock()
            before = c.pine.value
            for _ in range(4):
                c.pine.value += 25
                c._wiring.player_bolts.apply_boost()
            await self.flush()
            self.assertEqual(c.pine.value - before, 100 * max(1, multiplier))
            self.assertEqual(c.send_msgs.call_args.args[0][0]['data']['amount'], 1)
            self.assertEqual(c._ring_link_remainder, 0)

    async def test_incoming_is_not_boosted_or_echoed_and_duplicates_are_ignored(self):
        c = self.ctx
        data = {'source': -1, 'time': 10, 'amount': 100}
        await c._receive_ring_link(data)
        await c._receive_ring_link(data)
        c._wiring.player_bolts.apply_boost()
        await self.flush()
        self.assertEqual(c.pine.value, 41000)
        c.send_msgs.assert_not_called()

    async def test_pickup_between_ticks_survives_incoming_link(self):
        c = self.ctx
        c.pine.value += 100
        await c._receive_ring_link({'source': -1, 'time': 10, 'amount': 2})
        await self.flush()
        self.assertEqual(c.pine.value, 2200)
        self.assertEqual(c.send_msgs.call_args.args[0][0]['data']['amount'], 1)

    async def test_losses_clamp_and_never_echo(self):
        c = self.ctx
        await c._receive_ring_link({'source': -1, 'time': 1, 'amount': -100})
        self.assertEqual(c.pine.value, 0)
        await c._receive_ring_link({'source': -1, 'time': 2, 'amount': 10**9})
        self.assertEqual(c.pine.value, MAX_PLAYER_BOLTS)
        c._wiring.player_bolts.apply_boost()
        await self.flush()
        c.send_msgs.assert_not_called()

    async def test_spending_is_automatic_and_negative_fractions_truncate(self):
        c = self.ctx
        c.pine.value -= 100
        c._wiring.player_bolts.apply_boost()
        await self.flush()
        c.send_msgs.assert_not_called()
        c.pine.value -= 299
        c._wiring.player_bolts.apply_boost()
        await self.flush()
        c.send_msgs.assert_not_called()
        c.pine.value -= 2
        c._wiring.player_bolts.apply_boost()
        await self.flush()
        self.assertEqual(c.send_msgs.call_args.args[0][0]['data']['amount'], -1)
        self.assertEqual(c._ring_link_remainder, -1)

    async def test_grants_loads_and_disabled_changes_do_not_send(self):
        c = self.ctx
        c.pine.value += 35000
        c._wiring.player_bolts.rebaseline()
        c._wiring.player_bolts.apply_boost()
        await self.flush()
        c.send_msgs.assert_not_called()
        await c._set_ring_link_enabled(False)
        c.pine.value += 50000
        await c._set_ring_link_enabled(True)
        c._wiring.player_bolts.apply_boost()
        await self.flush()
        c.send_msgs.assert_not_called()

    async def test_invalid_self_and_out_of_game_packets_are_ignored(self):
        c = self.ctx
        for data in ({}, {'source': -1, 'time': 1, 'amount': True},
                     {'source': c._ring_link_source, 'time': 1, 'amount': 100}):
            await c._receive_ring_link(data)
        c._wiring.planet.is_ready = False
        await c._receive_ring_link({'source': -1, 'time': 1, 'amount': 100})
        self.assertEqual(c.pine.value, 1000)

    async def test_fixed_ratio_ignores_legacy_option_and_clipped_gain(self):
        c = self.ctx
        c.slot_data['ring_link_ratio'] = 50
        self.assertEqual(c._bolts_per_ring(), 400)
        c.pine.value = MAX_PLAYER_BOLTS - 200
        c._wiring.player_bolts.rebaseline()
        c.pine.value += 100
        c._wiring.player_bolts.apply_boost()
        await self.flush()
        self.assertEqual(c.pine.value, MAX_PLAYER_BOLTS)
        c.send_msgs.assert_not_called()
        self.assertEqual(c._ring_link_remainder, 200)


class TrapLinkTests(unittest.IsolatedAsyncioTestCase):
    async def test_agreed_mappings_send_and_receive_without_echo(self):
        c = LinkContext()
        with patch('worlds.rac_size_matters.client.trap_link.traps_ready', return_value=True), \
                patch('worlds.rac_size_matters.client.trap_link.activate_trap') as activate:
            for native, wire in TRAP_LINK_NAMES.items():
                c._send_trap_link(native)
                await asyncio.sleep(0)
                data = c.send_msgs.call_args.args[0][0]['data']
                self.assertEqual(data['trap_name'], wire)
                self.assertEqual(data['source'], 'Ratchet')
                c.send_msgs.reset_mock()
                data['source'] = 'Sonic'
                await c._receive_trap_link(data)
                if native == Rac5Traps.TRAP_DROPPED_AMMO:
                    activate.assert_called_with(c.pine, native, weapons=c._wiring.planet.weapons)
                elif native == Rac5Traps.TRAP_GADGETRON_DEBT:
                    activate.assert_called_with(c.pine, native, debt_percent=20)
                else:
                    activate.assert_called_with(c.pine, native)
                calls = activate.call_count
                await c._receive_trap_link(data)
                self.assertEqual(activate.call_count, calls)
                c.send_msgs.assert_not_called()

    async def test_aliases_weights_self_unknown_and_loading(self):
        c = LinkContext()
        with patch('worlds.rac_size_matters.client.trap_link.traps_ready', return_value=True) as ready, \
                patch('worlds.rac_size_matters.client.trap_link.activate_trap') as activate:
            data = {'source': 'Sonic', 'time': 1, 'trap_name': 'Reverse Controls Trap'}
            await c._receive_trap_link(data)
            activate.assert_called_once_with(c.pine, Rac5Traps.TRAP_REVERSE_CONTROLS)
            activate.reset_mock()
            c.slot_data['trap_weight'] = {Rac5Traps.TRAP_REVERSE_CONTROLS: 0}
            await c._receive_trap_link({**data, 'time': 2})
            await c._receive_trap_link({**data, 'source': c.auth})
            await c._receive_trap_link({**data, 'trap_name': 'Unknown Trap'})
            ready.return_value = False
            await c._receive_trap_link({**data, 'trap_name': 'Teleport Trap'})
            activate.assert_not_called()


class PacketRoutingTests(unittest.IsolatedAsyncioTestCase):
    async def test_worker_routes_only_matching_link_tags(self):
        from ..client.worker import GameWorker
        from ..client import protocol
        ctx = SimpleNamespace(_death_link_enabled=True, auth='Ratchet',
                              _receive_death_link=AsyncMock(), _receive_ring_link=AsyncMock(),
                              _receive_trap_link=AsyncMock())
        for tag, handler in (('RingLink', ctx._receive_ring_link),
                             ('TrapLink', ctx._receive_trap_link),
                             ('DeathLink', ctx._receive_death_link)):
            data = {'source': 'Other player'}
            await GameWorker.handle(ctx, (protocol.BOUNCED, [tag], data))
            await asyncio.sleep(0)
            handler.assert_awaited_once_with(data)
            others = [h for h in (ctx._receive_ring_link, ctx._receive_trap_link,
                                  ctx._receive_death_link) if h is not handler]
            for other in others:
                other.assert_not_awaited()
            handler.reset_mock()

    async def test_context_preserves_bounce_tags(self):
        from ..client.context import RACContext
        from ..client import protocol
        ctx = RACContext.__new__(RACContext)
        ctx._to_worker = Mock()
        with patch.object(RACContext.__mro__[1], 'on_package'):
            for tag in ('RingLink', 'TrapLink', 'DeathLink'):
                data = {'source': 'Other player'}
                ctx.on_package('Bounced', {'tags': [tag], 'data': data})
                ctx._to_worker.assert_called_with((protocol.BOUNCED, [tag], data))

    async def test_ap_trap_delivery_sends_once_and_does_not_replay(self):
        from ..client.vendor import InventoryMixin
        c = LinkContext()
        c._processed_trap_count = 0
        c.game = 'Ratchet'
        c.item_names = {'Ratchet': {1: Rac5Traps.TRAP_REVERSE_CONTROLS}}
        c.items_received = [SimpleNamespace(item=1)]
        c._log = Mock()
        with patch('worlds.rac_size_matters.client.vendor.traps_ready', return_value=True), \
                patch('worlds.rac_size_matters.client.vendor.activate_trap'):
            InventoryMixin._grant_new_trap_items(c)
            InventoryMixin._grant_new_trap_items(c)
            await asyncio.sleep(0)
        c.send_msgs.assert_awaited_once()
        self.assertEqual(c.send_msgs.call_args.args[0][0]['data']['trap_name'], 'Confusion Trap')

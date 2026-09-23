import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from .test_client_gameplay import GameMemory
from ..client.deathlink import DeathLinkMixin, PlayerState
from ..core.player import PlayerInventory
from ..core.address_maps import CHEATS, CURRENT_PLANET_ADDRESS
from ..core.structs.game import TransitionGateStruct, TRANSITION_GATE_IDLE
from ..core import traps


class DeathHarness(DeathLinkMixin):
    def __init__(self):
        self.pine = GameMemory()
        player = PlayerInventory(self.pine)
        player.set_base(1)
        player.health = 5.0
        self._wiring = SimpleNamespace(planet=SimpleNamespace(planet_id=1, is_ready=True, player=player), vendor_active=False)
        self.psp_connected = self._death_link_enabled = True
        self._last_death_link = 0
        self._psp_lock = asyncio.Lock()
        self._log = self._write_notification_text = Mock()


class TestDeathLinkLifecycle(unittest.IsolatedAsyncioTestCase):
    async def test_psp_widths_preserve_neighbouring_fields(self):
        ctx = DeathHarness()
        player = ctx._wiring.planet.player
        ctx.pine.write_int8(player.movement_addr+1, 0xAB)
        ctx.pine.write_float(player.health_addr+4, 11.0)
        await ctx._receive_death_link({'time': 1, 'source': 'Other'})
        self.assertEqual(player.health, 0.0)
        self.assertEqual(player.movement_state, PlayerState.VoidDeath)
        self.assertEqual(ctx.pine.read_int8(player.movement_addr+1), 0xAB)
        self.assertEqual(player.max_health, 11.0)
        self.assertFalse(ctx._death_link_pending)

    async def test_death_waits_for_loading_and_vendor_close(self):
        ctx = DeathHarness()
        ctx.pine.write_int32(TransitionGateStruct.BASE_ADDRESS, 0)
        await ctx._receive_death_link({'time': 1})
        self.assertTrue(ctx._death_link_pending)
        self.assertEqual(ctx._wiring.planet.player.health, 5.0)
        ctx.pine.write_int32(TransitionGateStruct.BASE_ADDRESS, TRANSITION_GATE_IDLE)
        ctx._wiring.vendor_active = True
        ctx._poll_death_link()
        self.assertEqual(ctx._wiring.planet.player.health, 5.0)
        ctx._wiring.vendor_active = False
        ctx._poll_death_link()
        self.assertEqual(ctx._wiring.planet.player.health, 0.0)

    async def test_changed_overlay_is_not_written(self):
        ctx = DeathHarness()
        ctx.pine.write_int8(CURRENT_PLANET_ADDRESS, 3)
        before = bytes(ctx.pine.data)
        await ctx._receive_death_link({'time': 1})
        self.assertEqual(bytes(ctx.pine.data), before)
        self.assertTrue(ctx._death_link_pending)

    async def test_received_death_is_not_echoed_after_a_slow_death_animation(self):
        ctx = DeathHarness()
        await ctx._receive_death_link({'time': 1})
        ctx._last_death_link = 0
        ctx._send_death_link_from_sync(PlayerState.VoidDeath)
        self.assertEqual(ctx._last_death_link, 0)
        ctx._wiring.planet.player.movement_state = PlayerState.Alive
        ctx._poll_death_link()
        self.assertFalse(ctx._death_link_applied)

    async def test_invalid_and_disabled_events_do_not_write(self):
        ctx = DeathHarness()
        before = bytes(ctx.pine.data)
        for timestamp in ('bad', float('nan'), float('inf')):
            await ctx._receive_death_link({'time': timestamp})
        ctx._death_link_enabled = False
        await ctx._receive_death_link({'time': 1})
        self.assertEqual(bytes(ctx.pine.data), before)


class TestTrapLifecycle(unittest.TestCase):
    def setUp(self):
        self.memory = GameMemory()
        self.name = next(iter(traps.ALL_TRAPS))
        self.bit = traps._CHEAT_BITS[self.name]
        traps.set_trap_durations({self.name: 10}, self.memory)

    def test_stack_expire_and_preserve_other_cheats(self):
        self.memory.write_int8(CHEATS, 1)
        with patch.object(traps.time, 'monotonic', return_value=100):
            traps.activate_trap(self.memory, self.name)
        with patch.object(traps.time, 'monotonic', return_value=105):
            traps.activate_trap(self.memory, self.name)
        with patch.object(traps.time, 'monotonic', return_value=119):
            traps.reconcile_traps(self.memory)
        self.assertEqual(self.memory.read_int8(CHEATS), 1 | self.bit)
        with patch.object(traps.time, 'monotonic', return_value=120):
            traps.reconcile_traps(self.memory)
        self.assertEqual(self.memory.read_int8(CHEATS), 1)

    def test_reconnect_restores_remaining_effect(self):
        with patch.object(traps.time, 'monotonic', return_value=100):
            traps.activate_trap(self.memory, self.name)
            traps.suspend_traps(self.memory)
        self.assertEqual(self.memory.read_int8(CHEATS), 0)
        with patch.object(traps.time, 'monotonic', return_value=105):
            traps.reconcile_traps(self.memory)
        self.assertEqual(self.memory.read_int8(CHEATS), self.bit)
        with patch.object(traps.time, 'monotonic', return_value=120):
            traps.reconcile_traps(self.memory)
        self.assertEqual(self.memory.read_int8(CHEATS), 0)

    def test_failed_activation_does_not_extend_the_retry(self):
        with patch.object(traps.time, 'monotonic', return_value=100):
            with patch.object(self.memory, 'write_int8', side_effect=ConnectionError):
                with self.assertRaises(ConnectionError):
                    traps.activate_trap(self.memory, self.name)
            traps.activate_trap(self.memory, self.name)
        with patch.object(traps.time, 'monotonic', return_value=111):
            traps.reconcile_traps(self.memory)
        self.assertEqual(self.memory.read_int8(CHEATS), 0)

    def test_sessions_and_seed_options_are_isolated(self):
        other = GameMemory()
        with patch.object(traps.time, 'monotonic', return_value=100):
            traps.activate_trap(self.memory, self.name)
            traps.reconcile_traps(other)
            traps.set_trap_durations({}, self.memory)
            traps.reconcile_traps(self.memory)
        self.assertEqual(other.read_int8(CHEATS), 0)
        self.assertEqual(self.memory.read_int8(CHEATS), 0)
        self.assertEqual(traps._state(self.memory).durations, traps.TRAP_DURATIONS)

    def test_loading_defers_delivery_and_expiry_writes(self):
        with patch.object(traps.time, 'monotonic', return_value=100):
            traps.activate_trap(self.memory, self.name)
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS, 0)
        before = bytes(self.memory.data)
        with patch.object(traps.time, 'monotonic', return_value=120):
            traps.reconcile_traps(self.memory)
            with self.assertRaises(RuntimeError):
                traps.activate_trap(self.memory, self.name)
        self.assertEqual(bytes(self.memory.data), before)
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS, TRANSITION_GATE_IDLE)
        with patch.object(traps.time, 'monotonic', return_value=120):
            traps.reconcile_traps(self.memory)
        self.assertEqual(self.memory.read_int8(CHEATS), 0)

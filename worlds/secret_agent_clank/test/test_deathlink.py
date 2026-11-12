import asyncio
import struct
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from ..client import DeathLinkMixin, SACContext
from ..core import ActivePlayer, Core, RuntimeSymbols
from .test_runtime import TEST_BUILD, Memory
from ..core.patches.loader_state import LoaderStateReader
from ..core.patches.asm import packed, jump
from .mips_cpu import CPU
from ..core.mission_failure import MissionFailure
from ..client.context import SACContext
from ..client.command_processor import SACCommandProcessor


class DeathDetectionTests(unittest.TestCase):
    def setUp(self):
        self.memory = Memory()
        self.core = Core(self.memory, permanent_build=TEST_BUILD)
        self.case = self.core.case
        self.core._strip_all_inventories = Mock()
        self.core._reapply_all_inventories = Mock()
        self.core.wire(send_location=Mock(), death_link_enabled=lambda: True, send_deathlink=Mock())
        self.case.case_id = 1
        self.case.is_ready = True
        self.case.active_player.pointer_address = 0x110000
        self.memory.write_int32(0x110000, 0x120000)
        self.memory.batch_write_int32([(0x206328, 1), (0x206324, 0xFFFFFFFF)])
        self.memory.write_int32(LoaderStateReader.STATE, 5)
        self.memory.write_int32(0x206338, 3)
        self.health(10)
        self.bind_ratchet_state()
        self.state(0)

    def bind_ratchet_state(self):
        self.case.active_player.state_kind = "Ratchet"
        self.case.active_player.state_offset = 0xAB4

    def state(self, value, player=0x120000):
        self.memory.write_bytes(player + 0xAB4, struct.pack("<h", value))

    def health(self, value, maximum=10):
        self.memory.write_bytes(0x120274, struct.pack('<2f', value, maximum))

    def install_failure_hook(self):
        render = 0x140000
        self.memory.write_bytes(render + 0x14, packed([jump(0x160000, True), 0x240403A6]))
        cursor = 0x150000
        def allocate(data):
            nonlocal cursor
            address = cursor
            self.memory.write_bytes(address, data)
            cursor += len(data)
            return address
        patches = self.case.mission_failure.prepare(
            {'CLANK_MissionFailedText__FPv': render, 'GetStr__Fi': 0x160000}, allocate)
        for edit in patches:
            self.memory.write_bytes(edit.address, edit.replacement)
        return render + 0x14

    def render_failure(self, render):
        cpu = CPU(self.memory)
        sp = cpu.r[29]
        cpu.run(render, stop=0x160000)
        self.assertEqual(cpu.r[29], sp)
        self.assertEqual(cpu.r[31], render + 8)
        self.assertEqual(cpu.r[4], 934)

    def test_failure_at_full_health_counts_once_and_rearms_after_reload(self):
        render = self.install_failure_hook()
        for _ in range(3):
            self.render_failure(render)
            self.case.check_death()
        self.core.send_deathlink.assert_called_once_with('failed a mission')
        self.core._reapply_all_inventories.assert_not_called()
        self.install_failure_hook()  # Next module starts with a fresh latch.
        self.case.check_death()
        self.render_failure(render)
        self.case.check_death()
        self.assertEqual(self.core.send_deathlink.call_count, 2)

    def test_failure_without_player_or_during_loading_is_counted(self):
        render = self.install_failure_hook()
        self.memory.write_int32(0x110000, 0)
        self.case.is_ready = False
        self.render_failure(render)
        self.case.check_mission_failure()
        self.core.send_deathlink.assert_called_once()

    def test_gadgetbot_failure_rearms_on_fresh_module_without_player_states(self):
        self.case.active_player.state_offset = None
        for _ in range(2):
            render = self.install_failure_hook()
            self.case.check_death()
            self.render_failure(render)
            self.case.check_death()
        self.assertEqual(self.core.send_deathlink.call_count, 2)

    def test_failure_after_state_death_or_received_death_is_not_duplicated(self):
        for received in (False, True):
            self.setUp()
            render = self.install_failure_hook()
            self.case.check_death()
            if received:
                self.case.receive_death()
            else:
                self.state(0x23)
                self.case.check_death()
            self.render_failure(render)
            self.case.check_death()
            self.assertEqual(self.core.send_deathlink.call_count, 0 if received else 1)

    def test_failure_respects_amnesty_and_disabled_deathlink(self):
        render = self.install_failure_hook()
        self.core.death_amnesty = lambda: 1
        self.render_failure(render)
        self.case.check_death()
        self.assertEqual(self.core._death_count, 1)
        self.core.send_deathlink.assert_not_called()
        self.install_failure_hook()
        self.case.check_death()
        self.core.death_link_enabled = lambda: False
        self.render_failure(render)
        self.case.check_death()
        self.core.send_deathlink.assert_not_called()

    def test_replaced_module_does_not_report_stale_failure(self):
        render = self.install_failure_hook()
        self.render_failure(render)
        self.memory.write_int32(render, 0)
        self.case.check_mission_failure()
        self.core.send_deathlink.assert_not_called()

    def test_local_death_once_then_rearm_after_respawn(self):
        self.case.check_death()
        for value in (0x23, 0x23, 0x24):
            self.state(value)
            self.case.check_death()
        self.core.send_deathlink.assert_called_once_with('died (Ratchet state 0x23)')
        self.state(0)
        self.case.check_death()
        self.core._reapply_all_inventories.assert_called_once()
        self.state(0x23)
        self.case.check_death()
        self.assertEqual(self.core.send_deathlink.call_count, 2)

    def test_health_alone_never_counts_as_death(self):
        self.case.check_death()
        for health in (0, -1, float('nan')):
            self.health(health)
            self.case.check_death()
        self.core.send_deathlink.assert_not_called()
        self.health(10)
        self.state(0x23)
        self.case.check_death()
        self.core.send_deathlink.assert_called_once_with('died (Ratchet state 0x23)')

    def test_all_ratchet_death_states_and_adjacent_live_states(self):
        for state in range(0x21, 0x2E):
            self.state(state)
            sample = self.case.active_player.death_state_sample()
            self.assertEqual(sample[1] is not None, 0x22 <= state <= 0x2C)

    def test_clank_named_deaths_report_cause_without_health(self):
        player = self.case.active_player
        player.state_kind, player.state_offset = 'Clank', 0xAB8
        player.death_vtables = {0x150000: 'died', 0x150100: 'fell to their death',
            0x150200: 'drowned', 0x150300: 'failed a mission',
            0x150400: 'failed a mission by falling'}
        player.state_vtables = set(player.death_vtables) | {0x150500}
        self.memory.write_int32(0x120AB8, 0x140000)
        for vtable, cause in player.death_vtables.items():
            self.memory.write_int32(0x140008, 0x150500)
            self.case.check_death()
            self.memory.write_int32(0x140008, vtable)
            self.case.check_death()
            self.core.send_deathlink.assert_called_with(cause)
        self.assertEqual(self.core.send_deathlink.call_count, 5)
        self.memory.write_int32(0x140008, 0)
        self.assertIsNone(player.death_state_sample())

    def test_amnesty_accumulates_across_respawns_and_resets_after_send(self):
        self.core.death_amnesty = lambda: 1
        for expected in (0, 1, 1, 2):
            self.state(0)
            self.case.check_death()
            self.state(0x23)
            self.case.check_death()
            self.assertEqual(self.core.send_deathlink.call_count, expected)

    def test_uninitialized_invalid_and_loading_samples_do_not_send(self):
        for value in (0x23, -1, 0x7FFF):
            self.state(value)
            self.case.check_death()
        self.memory.write_int32(0x110000, 0)
        self.case.check_death()
        self.memory.write_int32(0x110000, 0x120000)
        self.state(0)
        self.case.check_death()
        self.case.is_ready = False
        self.state(0x23)
        self.case.check_death()
        self.core.send_deathlink.assert_not_called()

    def test_received_death_is_not_echoed_and_later_local_death_is_sent(self):
        self.case.check_death()
        self.assertTrue(self.case.receive_death())
        for _ in range(5):
            self.case.check_death()
        self.core.send_deathlink.assert_not_called()
        self.assertEqual(self.core._death_count, 0)
        self.state(0x23)
        self.case.check_death()
        self.core.send_deathlink.assert_not_called()
        self.state(0)
        self.case.check_death()
        self.state(0x23)
        self.case.check_death()
        self.core.send_deathlink.assert_called_once()

    def test_received_death_during_transition_cannot_write_old_player(self):
        self.memory.write_int32(0x206324, 2)
        self.memory.writes.clear()
        self.assertFalse(self.case.receive_death())
        self.assertEqual(self.memory.writes, [])

    def test_disabled_deathlink_does_not_send(self):
        self.core.death_link_enabled = lambda: False
        self.case.check_death()
        self.state(0x23)
        self.case.check_death()
        self.core.send_deathlink.assert_not_called()

    def test_respawn_after_module_reload_rearms_detection(self):
        self.case.check_death()
        self.state(0x23)
        self.case.check_death()
        self.case.check_transition(allow_bind=False)
        self.assertIsNone(self.case.active_player.pointer_address)
        self.case.active_player.pointer_address = 0x110000
        self.bind_ratchet_state()
        self.case.is_ready = True
        self.state(0)
        self.case.check_death()
        self.state(0x23)
        self.case.check_death()
        self.assertEqual(self.core.send_deathlink.call_count, 2)

    def test_player_pointer_relocation_uses_current_character(self):
        self.case.check_death()
        self.memory.write_int32(0x110000, 0x130000)
        self.memory.write_bytes(0x130274, struct.pack('<2f', 10, 10))
        self.state(0x23)  # The previous character is no longer active.
        self.case.check_death()
        self.core.send_deathlink.assert_not_called()
        self.state(0x23, player=0x130000)
        self.case.check_death()
        self.core.send_deathlink.assert_called_once()

    def test_native_accessors_in_local_captures(self):
        verified = 0
        research = Path(__file__).parents[1] / '.research'
        captures = [*research.glob('*.ram'), *research.glob('prison_skin_snapshot.bin')]
        for capture in captures:
            raw = capture.read_bytes()
            symbols = RuntimeSymbols.parse(raw[:0x1000000], 0)
            if 'PLAYER_GetHitPoints__Fv' not in symbols:
                continue
            with self.subTest(capture=capture.name):
                memory = Memory()
                memory.data[:] = raw
                player = ActivePlayer(memory)
                player.bind_runtime(symbols)
                self.assertIsNotNone(player.pointer_address)
                self.assertIn(player.state_kind, ('Ratchet', 'Clank'))
                failure = MissionFailure(memory)
                failure.prepare(symbols, lambda data: 0x150000)
                if 'CLANK_MissionFailedText__FPv' in symbols:
                    self.assertIsNotNone(failure.binding)
                verified += 1
        if not verified:
            self.skipTest('Local player captures unavailable')


class DeathNotificationTests(unittest.TestCase):
    def test_worker_event_sends_archipelago_deathlink_bounce(self):
        ctx = SimpleNamespace(_notification_slot=('seed', 0, 1),
            _death_link_enabled=True, last_death_link=0,
            auth='Clank player', current_planet='', _worker=SimpleNamespace(request=Mock()))
        ctx.send_death = AsyncMock()
        ctx._send_death_link_from_sync = lambda value: DeathLinkMixin._send_death_link_from_sync(ctx, value)
        tasks = []
        with patch('worlds.secret_agent_clank.client.deathlink.async_start',
                   side_effect=tasks.append):
            SACContext._worker_event(ctx, 'death', {'cause': 'drowned', 'planet': 'Boltaire Museum'}, ('seed', 0, 1))
        self.assertEqual(len(tasks), 2)
        ctx._worker.request.assert_called_once_with('death_sent', 'Clank player drowned on Boltaire Museum.')
        ctx.send_death.assert_called_once_with('Clank player drowned on Boltaire Museum.')
        self.assertEqual(ctx.current_planet, 'Boltaire Museum')
        for task in tasks:
            task.close()


class DeathLinkReceiveTests(unittest.IsolatedAsyncioTestCase):
    async def test_received_deathlink_sends_source_and_cause_to_the_game(self):
        ctx = SimpleNamespace(pine_connected=True, _pine_lock=asyncio.Lock(),
                              _worker=SimpleNamespace(request=AsyncMock()))
        await DeathLinkMixin._receive_death_link(ctx, {'time': 1, 'source': 'Bob', 'cause': 'Bob fell.'})
        ctx._worker.request.assert_awaited_once_with('death', ('Bob', 'Bob fell.'))


    async def test_only_newer_deathlinks_reach_the_game(self):
        ctx = SACContext.__new__(SACContext)
        ctx.last_death_link, ctx._death_link_enabled = 5.0, True
        with patch('worlds.secret_agent_clank.client.deathlink.async_start') as start:
            ctx.on_deathlink({'time': 5.0, 'source': 'Me', 'cause': 'Me died.'})  # the one we sent
            ctx.on_deathlink({'time': 4.0, 'source': 'Bob', 'cause': 'Bob fell.'})
            start.assert_not_called()
            ctx.on_deathlink({'time': 6.0, 'source': 'Bob', 'cause': 'Bob fell.'})
            start.assert_called_once()
            start.call_args.args[0].close()
        self.assertEqual(ctx.last_death_link, 6.0)


class DeathLinkCommandTests(unittest.TestCase):
    def test_toggle_deathlink_flips_the_current_setting(self):
        for current in (False, True):
            with self.subTest(current=current):
                ctx = SimpleNamespace(_death_link_enabled=current, _set_death_link_enabled=Mock())
                processor = SACCommandProcessor.__new__(SACCommandProcessor)
                processor.ctx = ctx
                with patch('worlds.secret_agent_clank.client.command_processor.async_start'):
                    self.assertTrue(processor._cmd_toggle_deathlink())
                ctx._set_death_link_enabled.assert_called_once_with(not current)

import asyncio
import os
import time
import unittest
from unittest.mock import Mock, patch

from ..client import GameRuntime, GameWorker
from ..constants import GoalOptions, MissionsOptions
from ..core import death_sent_text, death_text
from .test_runtime import TEST_BUILD, Memory
from ..core.patches.identity import WrongPatchedGame
from ..constants.missions import MISSION_COMPLETE_NAME
from ..constants.planets import SACCases


class TestRuntime:
    __test__ = False

    def __init__(self, emit):
        self.emit = emit
        self.calls = 0

    def dispatch(self, command, payload):
        self.calls += 1
        if command == 'slow':
            self.emit('log', 'patching', None)
            time.sleep(payload)
            self.emit('location', 'test check', ('seed', 0, 1))
        elif command == 'crash':
            os._exit(4)
        elif command == 'fail':
            raise ValueError('validation failed')
        return (os.getpid(), self.calls, command)

    def disconnect(self):
        pass


class WorkerProcessTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.events = []
        self.worker = GameWorker(lambda *event: self.events.append(event), runtime_factory=TestRuntime)
        self.addAsyncCleanup(self.worker.close)
        self.pid, _, _ = await self.worker.request('ready')
        self.assertNotEqual(self.pid, os.getpid())

    async def test_slow_work_does_not_block_event_loop_and_delivers_events(self):
        task = asyncio.create_task(self.worker.request('slow', 0.4))
        beats = 0
        while not task.done():
            await asyncio.sleep(0.02)
            beats += 1
        self.assertGreaterEqual(beats, 8)
        self.assertEqual((await task)[0], self.pid)
        self.assertEqual([event[0] for event in self.events], ['log', 'location'])

    async def test_concurrent_requests_are_serial_and_cancellation_keeps_replies_matched(self):
        task = asyncio.create_task(self.worker.request('slow', 0.2))
        await asyncio.sleep(0.05)
        task.cancel()
        following = asyncio.create_task(self.worker.request('after_cancel'))
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual((await following)[2], 'after_cancel')
        results = await asyncio.gather(*(self.worker.request(str(i)) for i in range(10)))
        self.assertEqual([result[2] for result in results], [str(i) for i in range(10)])
        self.assertEqual({result[0] for result in results}, {self.pid})

    async def test_error_is_returned_and_reconnect_uses_same_worker(self):
        with self.assertRaisesRegex(RuntimeError, 'validation failed'):
            await self.worker.request('fail')
        await self.worker.request('disconnect')
        self.assertEqual((await self.worker.request('connect'))[0], self.pid)

    async def test_worker_death_is_detected_without_spawning_replacement(self):
        with self.assertRaises((EOFError, ConnectionError, OSError)):
            await self.worker.request('crash')
        with self.assertRaisesRegex(ConnectionError, 'restart'):
            await self.worker.request('connect')
        self.assertFalse(self.worker.process.is_alive())

    async def test_shutdown_reaps_process(self):
        self.assertTrue(await self.worker.close())
        self.assertFalse(self.worker.process.is_alive())

    async def test_shutdown_waits_for_active_patch(self):
        task = asyncio.create_task(self.worker.request('slow', 0.3))
        await asyncio.sleep(0.05)
        self.assertTrue(await self.worker.close())
        self.assertEqual((await task)[2], 'slow')
        self.assertFalse(self.worker.process.is_alive())

    async def test_hung_worker_times_out_and_is_reaped(self):
        self.worker.timeout = 0.1
        with self.assertRaises(TimeoutError):
            await self.worker.request('slow', 2)
        self.assertTrue(self.worker.broken)
        self.assertFalse(self.worker.process.is_alive())


class PatchedGameWorkerTests(unittest.TestCase):
    def test_identity_failure_drops_connection_without_restoration_or_commands(self):
        for command in ('tick', 'items', 'sync', 'effect', 'reset_traps', 'death', 'disconnect'):
            with self.subTest(command=command):
                pine = Memory()
                pine.disconnect = Mock()
                build = {'abi': 1, 'build_id': 'test-build', 'elf_crc': '12345678', 'loader_routine': 0x1C0000, 'modules': {}}
                with patch('worlds.secret_agent_clank.client.game_worker.Pine', return_value=pine):
                    runtime = GameRuntime(Mock(), permanent_build=build)
                runtime.connected = True
                runtime.core.close = Mock()
                runtime.core.native_runtime.verify = Mock(side_effect=WrongPatchedGame('different ISO'))
                with self.assertRaises(WrongPatchedGame):
                    runtime.dispatch(command, None)
                self.assertFalse(runtime.connected)
                runtime.core.close.assert_not_called()
                pine.disconnect.assert_called_once()
                self.assertEqual(pine.writes, [])


class GameRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.pine = Memory()
        self.pine.connect = Mock()
        self.pine.disconnect = Mock()
        self.pine.set_slot = Mock()
        self.pine.get_game_id = Mock(return_value='SCUS-97623')
        self.events = []
        with patch('worlds.secret_agent_clank.client.game_worker.Pine', return_value=self.pine) as factory:
            self.runtime = GameRuntime(lambda *event: self.events.append(event), permanent_build=TEST_BUILD)
            factory.assert_called_once_with()
        self.runtime.core.native_runtime.verify = Mock(return_value=None)
        self.runtime.core.native_runtime._gameplay_settled = Mock(return_value=True)

    def test_reconnect_uses_one_pine_and_closes_core_first(self):
        calls = []
        self.runtime.core.close = lambda: calls.append('restore')
        self.pine.disconnect.side_effect = lambda: calls.append('disconnect')
        for _ in range(2):
            self.runtime.dispatch('connect', 28011)
            self.runtime.dispatch('disconnect', None)
        self.assertIs(self.runtime.pine, self.pine)
        self.assertEqual(calls, ['restore', 'disconnect', 'restore', 'disconnect'])
        self.assertEqual(self.pine.connect.call_count, 2)

    def test_received_death_is_shown_on_the_hud(self):
        self.runtime.dispatch('connect', 28011)
        self.runtime.core.case.receive_death = Mock(return_value=True)
        self.assertTrue(self.runtime.dispatch('death', ('Bob', 'Bob fell.')))
        self.assertEqual(list(self.runtime.core.notifications.queue), [death_text('Bob', 'Bob fell.')])

    def test_sent_death_is_shown_on_the_hud(self):
        self.runtime.dispatch('death_sent', 'Me drowned on Hydrano.')
        self.assertEqual(list(self.runtime.core.notifications.queue), [death_sent_text('Me drowned on Hydrano.')])

    def test_location_needs_host_confirmation(self):
        self.runtime.allowed = {'check'}
        self.assertFalse(self.runtime.location('check'))
        self.assertEqual(self.events, [('location', 'check', None)])
        self.assertFalse(self.runtime.location('unselected'))
        self.assertEqual(len(self.events), 1)

    def test_connected_diagnostics_read_the_iso_startup_barrier(self):
        self.runtime.connected = True
        barrier = self.runtime.core.native_runtime.startup_barrier
        self.pine.write_int32(barrier.SIGNATURE_START, 0x3C020020)
        self.pine.writes.clear()
        info = self.runtime.diagnostic('sac_info')
        self.assertEqual(info['loader']['barrier_instruction'], '0x3C020020')
        self.assertFalse(info['startup_barrier_attached'])
        self.assertEqual(self.pine.writes, [])

    def test_failed_restore_still_disconnects(self):
        self.runtime.dispatch('connect', 28011)
        self.runtime.core.close = Mock(side_effect=RuntimeError('restore failed'))
        with self.assertRaisesRegex(RuntimeError, 'restore failed'):
            self.runtime.dispatch('disconnect', None)
        self.pine.disconnect.assert_called_once()
        self.assertFalse(self.runtime.connected)

    def test_wrong_game_never_ticks_and_disconnects(self):
        self.pine.get_game_id.return_value = 'wrong-game'
        with self.assertRaisesRegex(RuntimeError, 'Wrong game'):
            self.runtime.dispatch('connect', 28011)
        self.assertFalse(self.runtime.connected)
        self.pine.disconnect.assert_called_once()

    def test_configuration_events_and_slot_reset_keep_the_single_pine(self):
        identity = ('seed', 0, 1)
        self.runtime.dispatch('configure', (identity, {
            'goal': GoalOptions.PICK_AND_MIX, 'pick_and_mix_goals': ['defeat_klunk', 'chalice_of_power'],
            'death_link': True, 'all_missions': MissionsOptions.ALL}, {'check'}))
        core = self.runtime.core
        self.assertEqual(core.pick_and_mix_goals, (GoalOptions.DEFEAT_KLUNK, GoalOptions.CHALICE_OF_POWER))
        self.assertTrue(core.missions_all())
        core.keycards.chalice_collected = True
        core.missions._reported.add(MISSION_COMPLETE_NAME[SACCases.KLUNKS_LAIR])
        core._check_goal()
        core.send_deathlink('drowned')
        core.bolt_rewards.on_state_changed({'count': 1}, None)
        self.assertEqual([event[0] for event in self.events], ['goal', 'death', 'bolts'])
        self.assertEqual(self.events[1][1]['cause'], 'drowned')
        self.assertTrue(all(event[2] == identity for event in self.events))
        self.runtime.dispatch('configure', (('another-seed', 0, 1), {}, set()))
        self.assertIsNot(self.runtime.core, core)
        self.assertIs(self.runtime.core.pine, self.pine)
        self.assertFalse(self.runtime.core.missions._reported)

"""Real spawned-process IPC tests, without opening an emulator connection."""
import asyncio
import os
import time
import unittest
from unittest.mock import Mock, patch

from ..client.game_worker import GameRuntime
from ..client.worker_bridge import GameWorker
from .test_runtime import Memory


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


class GameRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.pine = Memory()
        self.pine.connect = Mock()
        self.pine.disconnect = Mock()
        self.pine.set_slot = Mock()
        self.pine.get_game_id = Mock(return_value='SCUS-97623')
        self.events = []
        with patch('worlds.secret_agent_clank.pypine.Pine', return_value=self.pine) as factory:
            self.runtime = GameRuntime(lambda *event: self.events.append(event))
            factory.assert_called_once_with()

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

    def test_location_needs_host_confirmation(self):
        self.runtime.allowed = {'check'}
        self.assertFalse(self.runtime.location('check'))
        self.assertEqual(self.events, [('location', 'check', None)])
        self.assertFalse(self.runtime.location('unselected'))
        self.assertEqual(len(self.events), 1)

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
        from ..options import Goal
        from ..constants.missions import MISSION_COMPLETE_NAME
        from ..constants.planets import SACCases
        identity = ('seed', 0, 1)
        self.runtime.dispatch('configure', (identity, {
            'goal': Goal.option_pick_and_mix, 'pick_and_mix_goals': ['defeat_klunk', 'chalice_of_power'],
            'death_link': True, 'all_missions': 1}, {'check'}))
        core = self.runtime.core
        self.assertEqual(core.pick_and_mix_goals, (Goal.option_defeat_klunk, Goal.option_chalice_of_power))
        self.assertTrue(core.missions_all())
        core.keycards.chalice_collected = True
        core.missions._reported.add(MISSION_COMPLETE_NAME[SACCases.KLUNKS_LAIR])
        core._check_goal()
        core.send_deathlink(1)
        core.bolt_rewards.on_state_changed({'count': 1}, None)
        self.assertEqual([event[0] for event in self.events], ['goal', 'death', 'bolts'])
        self.assertTrue(all(event[2] == identity for event in self.events))
        self.runtime.dispatch('configure', (('another-seed', 0, 1), {}, set()))
        self.assertIsNot(self.runtime.core, core)
        self.assertIs(self.runtime.core.pine, self.pine)
        self.assertFalse(self.runtime.core.missions._reported)

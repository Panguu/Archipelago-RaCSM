import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from ..client.command_processor import RACCommandProcessor
from ..client.worker import GameWorker


LINKS = ('death', 'ammo', 'ring', 'trap', 'ghost')


class LinkCommandParsingTests(unittest.TestCase):
    def test_commands_forward_status_and_normalized_actions(self):
        processor = RACCommandProcessor(SimpleNamespace(call_worker=Mock()))
        for name in LINKS:
            command = getattr(processor, f'_cmd_{name}link')
            for argument, expected in (('', ''), ('on', 'on'), ('OFF', 'off'), (' toggle ', 'toggle')):
                with self.subTest(link=name, argument=argument):
                    self.assertTrue(command(argument))
                    processor.ctx.call_worker.assert_called_with('cmd_link', f'{name}link', expected)
            processor.ctx.call_worker.reset_mock()
            self.assertFalse(command('invalid'))
            processor.ctx.call_worker.assert_not_called()

    def test_old_toggle_commands_are_removed(self):
        for name in (*LINKS, 'bolt'):
            self.assertFalse(hasattr(RACCommandProcessor, f'_cmd_toggle_{name}link'))


class LinkCommandStateTests(unittest.IsolatedAsyncioTestCase):
    async def test_status_is_read_only_and_explicit_states_are_idempotent(self):
        for name in LINKS:
            for enabled in (False, True):
                with self.subTest(link=name, enabled=enabled):
                    setter = AsyncMock()
                    worker = SimpleNamespace(**{
                        f'_{name}_link_enabled': enabled,
                        f'_set_{name}_link_enabled': setter,
                    })
                    with patch('worlds.rac_size_matters.client.worker.logger.info') as log:
                        await GameWorker.cmd_link(worker, f'{name}link')
                        log.assert_called_once_with(f"[RAC] {name.title()} Link is {'on' if enabled else 'off'}.")
                    setter.assert_not_awaited()
                    await GameWorker.cmd_link(worker, f'{name}link', 'on' if enabled else 'off')
                    setter.assert_not_awaited()
                    await GameWorker.cmd_link(worker, f'{name}link', 'off' if enabled else 'on')
                    setter.assert_awaited_once_with(not enabled)
                    setter.reset_mock()
                    await GameWorker.cmd_link(worker, f'{name}link', 'toggle')
                    setter.assert_awaited_once_with(not enabled)

    async def test_invalid_worker_requests_do_not_change_state(self):
        worker = SimpleNamespace()
        await GameWorker.cmd_link(worker, 'unknown', 'on')
        await GameWorker.cmd_link(worker, 'ringlink', 'invalid')


class LinkTagBatchTests(unittest.IsolatedAsyncioTestCase):
    def make_context(self):
        from ..client.context import RACContext
        ctx = RACContext.__new__(RACContext)
        ctx.tags = {"AP", "Custom", "BoltLink", "GhostLink"}
        ctx.server = SimpleNamespace(socket=SimpleNamespace(closed=False))
        ctx.send_msgs = AsyncMock()
        return ctx

    async def test_initial_batch_sends_only_complete_tags_and_removes_stale_links(self):
        import asyncio
        from ..client import protocol
        ctx = self.make_context()
        ctx._on_worker_message((protocol.UPDATE_LINK_TAGS, {
            "DeathLink": True, "AmmoLink": True, "BoltLink": False,
            "RingLink": True, "TrapLink": True, "GhostLink": False,
        }))
        await asyncio.sleep(0)
        expected = {"AP", "Custom", "DeathLink", "AmmoLink", "RingLink", "TrapLink"}
        self.assertEqual(ctx.tags, expected)
        ctx.send_msgs.assert_awaited_once_with([
            {"cmd": "ConnectUpdate", "tags": sorted(expected)}])

    async def test_unchanged_batch_does_not_send(self):
        ctx = self.make_context()
        await ctx._update_link_tags({"GhostLink": True, "RingLink": False})
        ctx.send_msgs.assert_not_awaited()

    async def test_disconnected_batch_updates_local_tags(self):
        ctx = self.make_context()
        ctx.server = None
        await ctx._update_link_tags({"BoltLink": False, "RingLink": True})
        self.assertEqual(ctx.tags, {"AP", "Custom", "GhostLink", "RingLink"})
        ctx.send_msgs.assert_not_awaited()

    async def test_individual_command_preserves_other_tags(self):
        ctx = self.make_context()
        await ctx._update_link_tag("TrapLink", True)
        expected = {"AP", "Custom", "BoltLink", "GhostLink", "TrapLink"}
        ctx.send_msgs.assert_awaited_once_with([
            {"cmd": "ConnectUpdate", "tags": sorted(expected)}])

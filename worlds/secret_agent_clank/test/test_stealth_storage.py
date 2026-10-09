import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from ..client.context import SACContext
from ..core.stealth import StealthState


class StealthStorageTests(unittest.IsolatedAsyncioTestCase):
    async def load_counts(self, stored):
        key = 'stealth-test'
        state = StealthState(None)
        ctx = SimpleNamespace(
            stored_data={}, _notification_slot=('seed', 0, 1),
            exit_event=asyncio.Event(), _stealth_key=lambda: key)

        async def send(messages):
            for message in messages:
                # MultiServer's default operation is a no-op. Initialization
                # comes from the packet-level default (otherwise integer 0).
                value = stored.get(message['key'], message.get('default', 0))
                for operation in message['operations']:
                    if operation['operation'] == 'replace':
                        value = operation['value']
                    else:
                        self.assertEqual(operation['operation'], 'default')
                stored[message['key']] = value
                if message.get('want_reply'):
                    ctx.stored_data[message['key']] = value

        async def request(command, counts):
            self.assertEqual(command, 'stealth')
            state.load(counts)
            # Subsequent count updates must work with the stored value too.
            stored[key].update({})

        ctx.send_msgs = AsyncMock(side_effect=send)
        ctx._worker = SimpleNamespace(request=AsyncMock(side_effect=request))
        await SACContext._load_stealth_state(ctx, ctx._notification_slot)
        self.assertTrue(state.loaded)
        return state, ctx

    async def test_new_slot_initializes_dictionary(self):
        stored = {}
        state, _ = await self.load_counts(stored)
        self.assertEqual(state.counts, {})
        self.assertEqual(stored, {'stealth-test': {}})

    async def test_legacy_zero_is_repaired(self):
        stored = {'stealth-test': 0}
        state, _ = await self.load_counts(stored)
        self.assertEqual(state.counts, {})
        self.assertEqual(stored['stealth-test'], {})

    async def test_existing_progress_is_preserved(self):
        stored = {'stealth-test': {'case': 7}}
        state, ctx = await self.load_counts(stored)
        self.assertEqual(state.counts, {'case': 7})
        self.assertEqual(stored['stealth-test'], {'case': 7})
        self.assertEqual(ctx.send_msgs.await_count, 1)

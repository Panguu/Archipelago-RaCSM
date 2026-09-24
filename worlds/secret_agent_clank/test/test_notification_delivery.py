"""Exercise the real client receipt path without a server or emulator."""
import asyncio
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock

from ..client.context import SACContext
from ..core.notifications import ItemNotifications


class NotificationDeliveryTests(unittest.IsolatedAsyncioTestCase):
    def context(self):
        hud = ItemNotifications(None)
        ctx = SimpleNamespace(
            slot=1, pine_connected=True, game='Secret Agent Clank',
            item_names={'Secret Agent Clank': {101: 'Progressive Wrench', 102: 'Test Trap'}},
            items_received=[], player_names={2: 'Pangu'}, _pine_lock=asyncio.Lock(),
            _notification_count=0,
            _wiring=SimpleNamespace(apply_inventory=Mock(), notifications=hud),
            _apply_new_traps=AsyncMock())
        return ctx, hud

    async def test_real_receipt_path_queues_item_sender_and_trap_colors_once(self):
        ctx, hud = self.context()
        ctx.items_received = [SimpleNamespace(item=101, player=2, flags=1),
                              SimpleNamespace(item=102, player=2, flags=4)]
        await SACContext._apply_received_items(ctx)
        self.assertEqual(len(hud.queue), 2)
        self.assertIn(b'\x90\x0dProgressive Wrench', hud.queue[0])
        self.assertIn(b'\x90\x0bPangu', hud.queue[0])
        self.assertIn(b'\x90\x03Test Trap', hud.queue[1])
        await SACContext._apply_received_items(ctx)
        self.assertEqual(len(hud.queue), 2)

    async def test_disconnected_receipt_waits_for_pine(self):
        ctx, hud = self.context()
        ctx.pine_connected = False
        ctx.items_received = [SimpleNamespace(item=101, player=2, flags=1)]
        await SACContext._apply_received_items(ctx)
        self.assertFalse(hud.queue)
        ctx.pine_connected = True
        await SACContext._apply_received_items(ctx)
        self.assertEqual(len(hud.queue), 1)

    async def test_initial_inventory_is_not_replayed(self):
        ctx, hud = self.context()
        ctx._notification_count = None
        ctx.items_received = [SimpleNamespace(item=101, player=2, flags=1)]
        await SACContext._apply_received_items(ctx)
        self.assertFalse(hud.queue)
        ctx.items_received.append(SimpleNamespace(item=102, player=2, flags=4))
        await SACContext._apply_received_items(ctx)
        self.assertEqual(len(hud.queue), 1)
        self.assertIn(b'Test Trap', hud.queue[0])

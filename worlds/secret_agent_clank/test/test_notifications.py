import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from NetUtils import NetworkItem

from ..core import ItemNotifications, death_text, receipt_text, sent_text
from .test_runtime import Memory
from ..client.context import SACContext


class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.p = Memory()
        self.p.write_int32 = lambda a, n: self.p.batch_write_int32([(a, n)])
        self.p.write_bytes = lambda a, b: self.p.data.__setitem__(slice(a, a + len(b)), b)
        self.n = ItemNotifications(self.p)
        self.n.binding = (0x110000, 0x120000, 0x120004, 0x120008, 0x110100, 0x120010, 0x120014, 0x120018)
        self.p.batch_write_int32([(0x206324, 0xFFFFFFFF), (0x206338, 3)])

    def test_colors_and_untrusted_names_are_bounded(self):
        text = receipt_text('X' * 200 + '\x90', 'Y\nZ', True)
        self.assertIn(b'\x90\x03', text)
        self.assertIn(b'from \x90\x0bY?Z', text)
        self.assertLess(len(text), 256)
        self.assertTrue(text.endswith(b'\0'))
        self.assertIn(b'\x90\x0d', receipt_text('Wrench', 'Pangu'))

    def test_native_message_and_pause_are_respected(self):
        self.n.enqueue('Wrench', 'Pangu')
        self.p.write_int32(0x120000, 60)
        self.n.tick()
        self.assertEqual(len(self.n.queue), 1)
        self.p.write_int32(0x120000, 0)
        self.p.write_int32(0x120018, 14)
        self.n.tick()
        self.assertEqual(len(self.n.queue), 1)
        self.assertEqual(self.p.read_int32(0x120018), 14)

    def test_displays_one_receipt_without_changing_input_state(self):
        self.n.enqueue('Wrench', 'Pangu')
        self.n.enqueue('Trap', 'Player', True)
        self.n.tick()
        self.assertEqual(len(self.n.queue), 1)
        self.assertEqual(self.p.read_int32(0x120000), 240)
        self.assertEqual(self.p.read_int32(0x120018), 0)
        self.assertEqual(self.p.read_int32(0x120010), 0xFFFFFFFF)
        self.assertEqual(self.p.read_int32(0x120014), 0xFFFFFFFF)
        self.assertIn(b'Wrench', self.p.read_bytes(0x110000, 256))
        self.n.tick()
        self.assertEqual(len(self.n.queue), 1)


class SentNotificationTests(unittest.TestCase):
    def test_sent_text_names_item_and_receiver(self):
        text = sent_text('Hookshot', 'Bob\nX', True)
        self.assertTrue(text.startswith(b'Sent \x90\x03Hookshot'))
        self.assertIn(b'to \x90\x0bBob?X', text)
        self.assertTrue(text.endswith(b'\0'))
        self.assertIn(b'\x90\x0d', sent_text('Hookshot', 'Bob'))

    def test_only_our_items_for_other_players_are_shown(self):
        ctx = SimpleNamespace(slot=1, _worker=SimpleNamespace(request=Mock(return_value=None)),
                              player_names={1: "Me", 2: "Bob"},
                              item_names=SimpleNamespace(lookup_in_slot=lambda item, slot: f"item{item}@{slot}"))
        cases = (
            (NetworkItem(7, 100, 1, 4), 2, ("item7@2", "Bob", True)),
            (NetworkItem(7, 100, 1, 0), 1, None),
            (NetworkItem(7, 100, 2, 0), 1, None),
        )
        for item, receiver, expected in cases:
            with self.subTest(item=item, receiver=receiver), \
                    patch("worlds.secret_agent_clank.client.context.async_start"):
                ctx._worker.request.reset_mock()
                SACContext._notify_sent_item(ctx, {"type": "ItemSend", "item": item, "receiving": receiver})
                if expected is None:
                    ctx._worker.request.assert_not_called()
                else:
                    ctx._worker.request.assert_called_once_with("sent", expected)


class DeathNotificationTextTests(unittest.TestCase):
    def test_death_text_names_source_and_cause(self):
        text = death_text('Bob\nX', 'Bob died on Hydrano.')
        self.assertTrue(text.startswith(b'DeathLink from \x90\x0bBob?X\x90\x01\n'))
        self.assertIn(b'\x90\x03Bob died on Hydrano.', text)
        self.assertTrue(text.endswith(b'\0'))
        self.assertLess(len(death_text('S' * 200, 'C' * 200)), 256)

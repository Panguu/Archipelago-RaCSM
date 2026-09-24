import unittest
from ..core.notifications import ItemNotifications, receipt_text
from .test_runtime import Memory


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

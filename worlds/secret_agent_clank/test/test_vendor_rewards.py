import struct
import unittest
from pathlib import Path
from unittest.mock import Mock

from ..client.vendor_scouts import VendorReward
from ..core.symbols import RuntimeSymbols
from ..core.vendor import VendorState
from ..core.vendor_rewards import VendorRewards
from .test_native_capture_plans import CaptureMemory


class VendorRewardsTests(unittest.TestCase):
    def test_automatic_cosmetics_preserve_transaction_and_restore(self):
        capture = Path(__file__).parents[1] / ".research/vendor_separation_baseline.bin"
        if not capture.exists():
            self.skipTest("Local vendor capture unavailable")
        p = CaptureMemory()
        p.data[:] = capture.read_bytes()
        p.get_game_id = lambda: "SCUS-97623"
        p.write_int32 = lambda a, v: p.batch_write_int32([(a, v)])
        symbols = RuntimeSymbols.parse(p.data[:0x1000000], 0)
        vendor = VendorState(p)
        self.assertTrue(vendor.bind_runtime(symbols))
        manager = VendorRewards(p, vendor, self.fail)
        hooks = Mock(patches=[])
        manager.text.prepare(symbols, hooks)
        p.write_int32(manager.text.timer, 0)
        row = vendor.selected_item()
        reward = VendorReward(1, 2, 1, "Progressive Wrench", "Pangu", 1)
        manager.scouts = Mock()
        manager.scouts.for_row = lambda r: reward if r.index == row.index else None
        before = vendor.read_items()
        price = p.read_int32(vendor.price_addr)
        manager.tick(symbols)
        self.assertTrue(manager.icon.installed)
        self.assertEqual(vendor.selected_item().icon, 73)
        self.assertEqual(p.read_int32(vendor.price_addr), price)
        for old, new in zip(before, vendor.read_items()):
            self.assertEqual(old._replace(icon=new.icon), new)
        self.assertIn(b"\x90\x02Progressive Wrench", p.read_bytes(manager.text.mailbox + 16, 88))
        manager.close()
        self.assertEqual(vendor.read_items(), before)
        self.assertFalse(manager.icon.installed)
        self.assertEqual(p.read_int32(manager.text.mailbox), 0)

    def test_native_hint_keeps_its_text_buffer(self):
        from ..core.patches.vendor_presentation import VendorPresentation
        p = CaptureMemory()
        text = VendorPresentation(p)
        text.mailbox, text.timer = 0x100000, 0x100100
        p.write_bytes(text.mailbox, b"Native hint\0")
        p.batch_write_int32([(text.timer, 1)])
        text.publish(0, None, None)
        self.assertEqual(p.read_bytes(text.mailbox, 12), b"Native hint\0")

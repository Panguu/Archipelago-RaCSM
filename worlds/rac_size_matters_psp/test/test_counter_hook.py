from contextlib import nullcontext
import unittest
from unittest.mock import Mock

from ..core.patches.counter import CounterHook, counter_payload, jump
from ..core.patches.storage import PatchStorage


class TestCounterHook(unittest.TestCase):
    def setUp(self):
        self.data = bytearray(0x10000)
        self.entry = 0x09008000
        self.original = bytes.fromhex("a0ffbd274009043c")
        self.data[0x8000:0x8008] = self.original
        self.memory = Mock()
        self.memory.paused.side_effect = nullcontext
        self.memory.get_game_id.return_value = "UCUS98633"
        self.memory._control._request.return_value = {"pc": self.entry + 8, "stepping": True}
        self.memory.read_bytes.side_effect = lambda address, size: bytes(self.data[address - 0x09000000:address - 0x09000000 + size])
        def write(address, data):
            offset = address - 0x09000000
            self.data[offset:offset + len(data)] = data
        self.memory.write_bytes.side_effect = write
        self.kernel = Mock()
        self.kernel.allocate.return_value = 123
        self.kernel.head.return_value = 0x09000000
        self.kernel.free.return_value = 0
        self.storage = PatchStorage(self.memory, self.kernel)
        self.storage.open()
        self.hook = CounterHook(self.memory, self.storage, self.entry, self.original, planet_id=1)

    def test_restore_precedes_free(self):
        self.hook.install()
        self.assertNotEqual(self.data[0x8000:0x8008], self.original)
        with self.assertRaises(RuntimeError):
            self.storage.close()
        self.hook.restore()
        self.assertEqual(self.data[0x8000:0x8008], self.original)
        self.storage.close()
        self.kernel.free.assert_called_once_with(123)

    def test_no_restore_or_free_while_cpu_inside_payload(self):
        self.hook.install()
        self.memory._control._request.return_value = {"pc": self.hook.code.address + 4, "stepping": True}
        self.memory.write_bytes.reset_mock()
        with self.assertRaises(RuntimeError):
            self.hook.restore()
        with self.assertRaises(RuntimeError):
            self.storage.close()
        self.memory.write_bytes.assert_not_called()
        self.kernel.free.assert_not_called()

    def test_overlay_change_does_not_restore_old_instructions(self):
        self.hook.install()
        self.data[0x8000] ^= 1
        self.memory.write_bytes.reset_mock()
        with self.assertRaises(RuntimeError):
            self.hook.restore()
        self.memory.write_bytes.assert_not_called()
        with self.assertRaises(RuntimeError):
            self.storage.close()

    def test_mismatch_has_no_payload_or_hook_writes(self):
        self.data[0x8000] ^= 1
        self.memory.write_bytes.reset_mock()
        with self.assertRaises(RuntimeError):
            self.hook.install()
        self.memory.write_bytes.assert_not_called()
        self.storage.close()

    def test_rejects_unrelocatable_prologue(self):
        with self.assertRaises(ValueError):
            counter_payload(0x09000040, 0x09000080, self.entry, bytes.fromhex("0800001000000000"))
        with self.assertRaises(ValueError):
            jump(0x09000000, 0x19000000)

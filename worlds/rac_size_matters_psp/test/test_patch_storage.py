import unittest
from unittest.mock import Mock

from ..core.patches.storage import PatchStorage


class TestPatchStorage(unittest.TestCase):
    def setUp(self):
        self.data = bytearray(0x4000)
        self.memory = Mock()
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

    def test_round_trip_and_nonoverlapping_buffers(self):
        self.storage.open()
        a = self.storage.reserve("code", 17)
        b = self.storage.reserve("data", 128, alignment=64)
        self.assertEqual(a.address, 0x09000040)
        self.assertEqual(b.address, 0x09000080)
        self.storage.write("data", b"hello", offset=3)
        self.assertEqual(self.data[0x83:0x88], b"hello")
        self.storage.close()
        self.storage.close()
        self.kernel.free.assert_called_once_with(123)

    def test_active_hook_prevents_free(self):
        self.storage.open()
        self.storage.retain("toast")
        with self.assertRaises(RuntimeError):
            self.storage.close()
        self.kernel.free.assert_not_called()
        self.storage.release("toast")
        self.storage.close()

    def test_state_change_prevents_writes_and_free(self):
        self.storage.open()
        self.storage.reserve("text", 8)
        self.data[0] ^= 1
        self.memory.write_bytes.reset_mock()
        with self.assertRaises(RuntimeError):
            self.storage.write("text", b"a")
        with self.assertRaises(RuntimeError):
            self.storage.close()
        self.memory.write_bytes.assert_not_called()
        self.kernel.free.assert_not_called()

    def test_recycled_uid_prevents_free(self):
        self.storage.open()
        self.kernel.head.return_value += 64
        with self.assertRaises(RuntimeError):
            self.storage.close()
        self.kernel.free.assert_not_called()

    def test_bounds_and_failed_reservation_preserve_layout(self):
        self.storage.open()
        with self.assertRaises(MemoryError):
            self.storage.reserve("large", 0x4000)
        allocation = self.storage.reserve("small", 4)
        self.assertEqual(allocation.address, 0x09000040)
        for offset, data in ((-1, b"a"), (1, b"1234")):
            with self.assertRaises(ValueError):
                self.storage.write("small", data, offset)
        with self.assertRaises(ValueError):
            self.storage.reserve("small", 4)

    def test_allocator_failure_never_writes(self):
        self.kernel.allocate.return_value = 0x800200d9
        with self.assertRaises(RuntimeError):
            self.storage.open()
        self.memory.write_bytes.assert_not_called()
        self.kernel.free.assert_not_called()

    def test_invalid_head_releases_known_block(self):
        self.kernel.head.return_value = 0x00123400
        with self.assertRaises(RuntimeError):
            self.storage.open()
        self.kernel.free.assert_called_once_with(123)
        self.memory.write_bytes.assert_not_called()

    def test_write_failure_releases_known_block(self):
        self.memory.write_bytes.side_effect = OSError("failure")
        with self.assertRaises(OSError):
            self.storage.open()
        self.kernel.free.assert_called_once_with(123)

    def test_free_failure_preserves_ownership(self):
        self.storage.open()
        self.kernel.free.return_value = 0x800200d9
        with self.assertRaises(RuntimeError):
            self.storage.close()
        self.assertEqual(self.storage.block_id, 123)

    def test_initialization_cleanup_failure_cannot_allocate_again(self):
        self.memory.write_bytes.side_effect = OSError("failure")
        self.kernel.free.return_value = 0x800200d9
        with self.assertRaises(OSError):
            self.storage.open()
        self.assertEqual(self.storage.block_id, 123)
        with self.assertRaises(RuntimeError):
            self.storage.open()
        self.kernel.allocate.assert_called_once()

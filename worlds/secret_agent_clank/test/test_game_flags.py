import unittest

from ..core.patches import GameFlags


class Memory:
    def __init__(self):
        self.data = bytearray(0x200000)
        self.writes = []

    def read_bytes(self, address, size):
        return bytes(self.data[address:address+size])

    def write_bytes(self, address, data):
        self.writes.append((address, data))
        self.data[address:address+len(data)] = data

    def batch_read(self, reads):
        return [int.from_bytes(self.read_bytes(address, size), "little") for size, address in reads]

    def batch_write(self, writes):
        for _size, address, data in writes:
            self.write_bytes(address, data)


class GameFlagsTests(unittest.TestCase):
    def setUp(self):
        self.pine = Memory()
        self.flags = GameFlags(self.pine)

    def prepare(self, record=True):
        return self.flags.prepare(address=0x110000, table=0x120000,
                                  fallback=0x130000, record=record)

    def test_prepare_preserves_encoding_and_does_not_write(self):
        for record in (False, True):
            self.prepare(record)
            self.assertEqual(self.flags.replacement,
                             GameFlags._build_routine(0x120000, 0x130000, record=record))
        self.assertEqual(self.pine.writes, [])

    def test_read_does_not_write_native_memory(self):
        self.prepare()
        self.pine.data[0x120000:0x120003] = bytes([0, 1, 2])
        self.assertEqual(self.flags.read()[:3], bytes([0, 1, 2]))
        self.assertEqual(self.pine.writes, [])

    def test_invalid_prepare_clears_previous_plan(self):
        self.prepare()
        with self.assertRaises(ValueError):
            self.flags.prepare(address=0x120000, table=0x120000, fallback=0x130000, record=True)
        with self.assertRaises(RuntimeError):
            self.flags.read()

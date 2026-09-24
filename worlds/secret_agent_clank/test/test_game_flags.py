import unittest

from ..core.patches.gameFlags import GameFlags


class Memory:
    def __init__(self):
        self.data = bytearray(0x200000)
        self.writes = []

    def read_bytes(self, address, size):
        return bytes(self.data[address:address+size])

    def write_bytes(self, address, data):
        self.writes.append((address, data))
        self.data[address:address+len(data)] = data


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

    def test_apply_and_read_are_separate(self):
        self.prepare().apply()
        self.assertEqual(self.pine.read_bytes(0x110000, len(self.flags.replacement)),
                         self.flags.replacement)
        self.pine.data[0x120000:0x120003] = bytes([0, 1, 2])
        writes = list(self.pine.writes)
        self.assertEqual(self.flags.read()[:3], bytes([0, 1, 2]))
        self.assertEqual(self.pine.writes, writes)

    def test_stale_code_is_not_overwritten(self):
        self.prepare()
        self.pine.data[0x110000] = 1
        with self.assertRaises(RuntimeError):
            self.flags.apply()
        self.assertEqual(self.pine.writes, [])

    def test_failed_write_rolls_back(self):
        self.prepare()
        original_write = self.pine.write_bytes
        def failing_write(address, data):
            original_write(address, data)
            if len(self.pine.writes) == 1:
                raise OSError("Connection interrupted after write")
        self.pine.write_bytes = failing_write
        with self.assertRaises(OSError):
            self.flags.apply()
        self.assertEqual(self.pine.read_bytes(0x110000, len(self.flags.original)),
                         self.flags.original)

    def test_invalid_prepare_clears_previous_plan(self):
        self.prepare()
        with self.assertRaises(ValueError):
            self.flags.prepare(address=0x120000, table=0x120000,
                               fallback=0x130000, record=True)
        with self.assertRaises(RuntimeError):
            self.flags.apply()
        with self.assertRaises(RuntimeError):
            self.flags.read()

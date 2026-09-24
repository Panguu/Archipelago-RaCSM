"""Arena save-counter regressions using the captured Max-Security module."""
import struct
import unittest
from pathlib import Path

from ..constants.planets import SACCases
from ..constants.ratchet_challenges import RATCHET_CHALLENGES_BY_CASE
from ..core.inventories.ratchet_challenges import RatchetChallengeInventory
from ..core.symbols import RuntimeSymbols
from .test_runtime import Memory


class RatchetChallengeTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).parents[1] / ".research/ratchet_max_security_wrench.bin"
        if not path.exists():
            self.skipTest("Local Max-Security capture not present")
        self.pine = Memory()
        self.pine.data[:] = path.read_bytes()
        self.symbols = RuntimeSymbols.parse(self.pine.data[:0x1000000], 0)
        self.reader = RatchetChallengeInventory(self.pine)
        self.assertTrue(self.reader.bind(self.symbols))
        self.base = self.pine.read_int32(self.reader.flags.pointer_address)
        self.pine.data[self.base+0x534:self.base+0x559] = bytes(0x25)
        self.names = RATCHET_CHALLENGES_BY_CASE[SACCases.MAX_SECURITY_CELLS]

    def test_max_security_all_five_win_counts(self):
        for i, count in enumerate((1, 2, 4, 128, 255)):
            self.pine.data[self.base+0x534+i] = count
        self.assertEqual(self.reader.check(), list(self.names))

    def test_entry_retry_confirmation_and_rebind(self):
        self.pine.data[self.base+0x534] = 2
        self.reader.sync()
        self.assertEqual(self.reader.check(), [self.names[0]])
        self.assertEqual(self.reader.check(), [self.names[0]])
        self.reader.confirm(self.names[0])
        self.reader.invalidate()
        self.assertEqual(self.reader.check(), [])
        self.assertTrue(self.reader.bind(self.symbols))
        self.reader.sync()
        self.assertEqual(self.reader.check(), [])

    def test_current_save_pointer_and_invalid_pointer(self):
        other = 0x1000000
        self.pine.data[other+0x534:other+0x559] = bytes(0x25)
        self.pine.data[other+0x535] = 1
        struct.pack_into("<I", self.pine.data, self.reader.flags.pointer_address, other)
        self.assertEqual(self.reader.check(), [self.names[1]])
        struct.pack_into("<I", self.pine.data, self.reader.flags.pointer_address, 0)
        self.assertEqual(self.reader.check(), [])

    def test_changed_signature_and_missing_exports_fail_closed(self):
        address = self.symbols.get("Arena_GetWinCount__FUiUi")
        self.pine.data[address] ^= 1
        self.assertFalse(self.reader.bind(self.symbols))
        self.assertEqual(self.reader.check(), [])
        self.assertFalse(self.reader.bind({}))
        self.assertEqual(self.reader.check(), [])

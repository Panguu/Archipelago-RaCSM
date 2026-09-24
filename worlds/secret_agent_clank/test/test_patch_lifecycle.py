import unittest

from ..core.patches.asm import Patch as PatchRecord
from ..core.patches.entitlements import Entitlements
from ..core.patches.patch import PatchSet
from .test_game_flags import Memory


class ExampleSet(PatchSet):
    def prepare(self):
        self.patches = [PatchRecord(0x110000, b"aaaa", b"bbbb"),
                        PatchRecord(0x110004, b"cccc", b"dddd")]
        return self.patches


class RoutineLifecycleTests(unittest.TestCase):
    def test_entitlement_prepare_apply_read(self):
        pine = Memory()
        routine = Entitlements(pine).prepare(address=0x110000, table=0x120000,
                                            gadget_base=0x130000, fallback=0x140000)
        self.assertEqual(pine.writes, [])
        routine.apply()
        pine.data[0x120000:0x120028] = bytes([2] * 40)
        pine.data[0x120028] = 7
        writes = list(pine.writes)
        self.assertEqual(routine.read(), {"flags": bytes([2] * 40), "initializations": 7})
        self.assertEqual(pine.writes, writes)

    def test_set_validates_all_sites_before_any_write(self):
        pine = Memory()
        pine.data[0x110000:0x110008] = b"aaaaXXXX"
        patch = ExampleSet(pine)
        patch.prepare()
        with self.assertRaises(RuntimeError):
            patch.apply()
        self.assertEqual(pine.writes, [])

    def test_set_rolls_back_both_sites_after_second_write_fails(self):
        pine = Memory()
        pine.data[0x110000:0x110008] = b"aaaacccc"
        patch = ExampleSet(pine)
        patch.prepare()
        write = pine.write_bytes
        def failing_write(address, data):
            write(address, data)
            if len(pine.writes) == 2:
                raise OSError("Interrupted second write")
        pine.write_bytes = failing_write
        with self.assertRaises(OSError):
            patch.apply()
        self.assertEqual(pine.read_bytes(0x110000, 8), b"aaaacccc")
        self.assertEqual(patch.read(), {0x110000: b"aaaa", 0x110004: b"cccc"})

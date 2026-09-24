import struct
import unittest

from ..core.patches.loader_gate import LoaderGate
from .test_runtime import Memory


class LoaderGateTests(unittest.TestCase):
    def setUp(self):
        self.p = Memory()
        self.p.write_int32 = lambda address, value: self.p.batch_write_int32([(address, value)])
        self.p.write_bytes = lambda address, data: self.p.data.__setitem__(slice(address, address + len(data)), data)
        self.p.get_game_id = lambda: "SCUS-97623"
        self.p.write_bytes(LoaderGate.SIGNATURE_START, struct.pack("<11I", *LoaderGate.SIGNATURE))
        self.gate = LoaderGate(self.p)

    def test_branch_yields_without_starting_module(self):
        displacement = LoaderGate.HELD & 0xFFFF
        self.assertEqual(LoaderGate.SITE + 4 + displacement * 4, 0x103D74)
        self.assertEqual(LoaderGate.SIGNATURE[6], 0x24426320)

    def test_only_completed_state_four_is_held(self):
        self.gate.arm()
        self.p.write_int32(LoaderGate.TARGET, 1)
        self.p.write_int32(LoaderGate.HANDLE, 0x200000)
        for state, status, expected in ((5, 1, None), (4, 0xFFFFFFFF, None), (4, 1, 1)):
            self.p.write_int32(LoaderGate.STATE, state)
            self.p.write_int32(LoaderGate.STATUS, status)
            self.assertEqual(self.gate.held_module(), expected)
        self.gate.release()
        self.assertEqual(self.p.read_int32(LoaderGate.SITE), LoaderGate.ORIGINAL)

    def test_signature_failure_prevents_patch(self):
        self.p.write_int32(LoaderGate.SITE + 4, 0)
        with self.assertRaises(RuntimeError):
            self.gate.arm()
        self.assertFalse(self.gate.armed)

    def test_title_module_zero_is_recognized_so_it_can_be_released(self):
        self.gate.arm()
        for address, value in ((LoaderGate.TARGET, 0), (LoaderGate.HANDLE, 0x200000),
                               (LoaderGate.STATE, 4), (LoaderGate.STATUS, 1)):
            self.p.write_int32(address, value)
        self.assertEqual(self.gate.held_module(), 0)
        self.gate.release()

    def test_unknown_replacement_is_not_overwritten(self):
        self.gate.arm()
        self.p.write_int32(LoaderGate.SITE, 0)
        with self.assertRaises(RuntimeError):
            self.gate.release()
        self.assertEqual(self.p.read_int32(LoaderGate.SITE), 0)

    def test_savestate_original_can_be_released(self):
        self.gate.arm()
        self.p.write_int32(LoaderGate.SITE, LoaderGate.ORIGINAL)
        self.gate.release()
        self.assertFalse(self.gate.armed)

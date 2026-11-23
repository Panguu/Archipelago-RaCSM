import struct
import unittest

from ..core.patches.identity import (
    CodeProbe, PatchedGameGuard, WrongPatchedGame, executable_crc, read_pcsx2_crc, stamp_executable,
)


class ReadOnlyPine:
    def __init__(self):
        self.crc = "1234abcd"
        self.code = b"native code"
        self.game = "SCUS-97623"

    def _send_request(self, request):
        if request != struct.pack("<IB", 5, 13):
            raise AssertionError("Identity check sent a memory write or unknown request")
        return struct.pack("<IBI", 18, 0, 9) + self.crc.encode() + b"\0"

    def get_game_id(self):
        return self.game

    def read_bytes(self, address, size):
        return self.code[:size]


class TestISOIdentity(unittest.TestCase):
    def test_elf_stamp_changes_crc_without_touching_segments(self):
        data = b"\x7fELF\x01\x01\x01" + bytes(249)
        stamped = stamp_executable(data, build_id="test-build", abi=1)
        self.assertEqual(stamped[:len(data)], data)
        self.assertNotEqual(executable_crc(stamped), executable_crc(data))
        self.assertEqual(stamped, stamp_executable(data, build_id="test-build", abi=1))
        with self.assertRaisesRegex(ValueError, "already"):
            stamp_executable(stamped, build_id="test-build", abi=1)

    def test_native_crc_algorithm(self):
        self.assertEqual(executable_crc(struct.pack("<III", 0x12345678, 0xDEADBEEF, 0x12345678)), "deadbeef")

    def test_guard_requires_disc_and_loaded_code(self):
        pine = ReadOnlyPine()
        guard = PatchedGameGuard("test", pine.crc, (CodeProbe(0x103000, pine.code),))
        guard.verify(pine)
        for attribute, value in (("crc", "293abc84"), ("game", "Other"), ("code", b"retail code")):
            original = getattr(pine, attribute)
            setattr(pine, attribute, value)
            with self.subTest(attribute=attribute), self.assertRaises(WrongPatchedGame):
                guard.verify(pine)
            setattr(pine, attribute, original)

    def test_malformed_uuid(self):
        pine = ReadOnlyPine()
        pine.crc = "not-a-crc"
        with self.assertRaises(WrongPatchedGame):
            read_pcsx2_crc(pine)

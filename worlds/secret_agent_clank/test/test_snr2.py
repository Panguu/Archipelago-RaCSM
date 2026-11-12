import struct
import unittest

from ..core.patches.snr2 import InvalidModule, SNR2Module, word


def module_fixture():
    data = bytearray(512)
    data[:4] = b"SNR2"
    for offset, value in ((4, 280), (8, 1), (12, 320), (16, 2), (40, 128), (44, len(data)), (52, 400)):
        struct.pack_into("<I", data, offset, value)
    data[256:270] = b"target\0import\0"
    struct.pack_into("<III", data, 320, 256, 192, 0x20000)
    struct.pack_into("<III", data, 332, 263, 0, 0x10000)
    struct.pack_into("<III", data, 280, 152, 0x104, 0)
    struct.pack_into("<7I", data, 128,
                     0x3C020001, 0x3C030001, 0x24428010, 0x0C000030, 0xC0, 0, 0x0C000000)
    # Two HI16 records share the next LO16; then J26 and a 32-bit pointer.
    stream = b"\x01" + struct.pack("<I", 128) + bytes((5, 4, 6, 7)) + bytes(5)
    data[400:400 + len(stream)] = stream
    return bytes(data)


class TestSNR2(unittest.TestCase):
    def test_relocation_and_imports(self):
        data = module_fixture()
        module = SNR2Module(data)
        for base in (0x800000, 0x908000):
            loaded, exports = module.relocate(base, {"import": 0x123450})
            self.assertEqual(exports["target"], base + 192)
            self.assertEqual(word(loaded, 128), 0x3C020000 | ((base + 0x8010 + 0x8000) >> 16))
            self.assertEqual(word(loaded, 132), 0x3C030000 | ((base + 0x8010 + 0x8000) >> 16))
            self.assertEqual(word(loaded, 136), 0x24420000 | ((base + 0x8010) & 65535))
            self.assertEqual(word(loaded, 140), 0x0C000000 | ((base + 192) >> 2))
            self.assertEqual(word(loaded, 144), base + 192)
            self.assertEqual(word(loaded, 152), 0x0C000000 | (0x123450 >> 2))
        self.assertEqual(module.data, data)

    def test_absolute_exports(self):
        data = bytearray(module_fixture())
        struct.pack_into("<II", data, 324, 0x10000, 0x40000)
        _, exports = SNR2Module(bytes(data)).relocate(0x800000, {"import": 0x123450})
        self.assertEqual(exports["target"], 0x10000)

    def test_null_symbol_relocates_against_module_base(self):
        data = bytearray(module_fixture())
        struct.pack_into("<I", data, 16, 3)
        struct.pack_into("<III", data, 344, 270, 0, 0)
        struct.pack_into("<I", data, 284, 0x204)
        loaded, _ = SNR2Module(bytes(data)).relocate(0x800000, {"import": 0x123450})
        self.assertEqual(word(loaded, 152), 0x0C200000)

    def test_missing_import(self):
        with self.assertRaisesRegex(InvalidModule, "Unresolved import"):
            SNR2Module(module_fixture()).relocate(0x800000, {})

    def test_unpaired_high(self):
        data = bytearray(module_fixture())
        data[406] = 6  # Replace LO16 by J26.
        with self.assertRaisesRegex(InvalidModule, "HI16"):
            SNR2Module(bytes(data)).relocate(0x800000, {"import": 0x123450})

    def test_invalid_records(self):
        for offset, value in ((44, 1), (4, 510), (12, 510), (52, 510), (280, 511), (284, 0xFF04)):
            data = bytearray(module_fixture())
            struct.pack_into("<I", data, offset, value)
            with self.subTest(offset=offset), self.assertRaises(InvalidModule):
                SNR2Module(bytes(data))

    def test_native_bitfield_relocation(self):
        data = bytearray(struct.pack("<I", 0xFFFFFFFF))
        SNR2Module._write(data, 0, 119, 0x12345)
        self.assertEqual(word(data, 0), 0xFFE0003F | ((0x12345 << 3) & 0x1FFFC0))


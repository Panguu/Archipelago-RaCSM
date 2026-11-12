import struct
import unittest

from ..core.patches.module_compiler import Fixup, ModuleEdit, compile_module
from ..core.patches.snr2 import InvalidModule, SNR2Module, word
from .test_snr2 import module_fixture


class TestModuleCompiler(unittest.TestCase):
    def test_replaced_low_half_preserves_surviving_high_halves(self):
        source = module_fixture()
        edited = compile_module(source, (ModuleEdit(136, source[136:140], struct.pack("<I", 0)),))
        for base in (0x328B00, 0x800000, 0x908000, 0x918010):
            original, _ = SNR2Module(source).relocate(base, {"import": 0x123450})
            result, _ = SNR2Module(edited).relocate(base, {"import": 0x123450})
            self.assertEqual(result[128:136], original[128:136])
            self.assertEqual(word(result, 136), 0)
            self.assertEqual(result[140:156], original[140:156])

    def test_new_local_jump_replaces_import_relocation(self):
        source = module_fixture()
        edit = ModuleEdit(152, source[152:156], struct.pack("<I", 0x0C000000),
                          (Fixup(0, 4, "target", 16),))
        edited = SNR2Module(compile_module(source, (edit,)))
        for base in (0x328B00, 0x800000, 0x908000):
            result, _ = edited.relocate(base, {"import": 0x123450})
            self.assertEqual(word(result, 152), 0x0C000000 | ((base + 208) >> 2))
        self.assertEqual(sum(r.offset == 152 for r in edited.import_relocations), 1)

    def test_new_absolute_high_low_pair(self):
        source = module_fixture()
        edit = ModuleEdit(128, source[128:140], struct.pack("<III", 0x3C020000, 0x24420000, 0),
                          (Fixup(0, 5, "import", 0x100), Fixup(4, 6, "import", 0x100)))
        result, _ = SNR2Module(compile_module(source, (edit,))).relocate(0x800000, {"import": 0x128000})
        self.assertEqual(word(result, 128), 0x3C020013)
        self.assertEqual(word(result, 132), 0x24428100)

    def test_invalid_edits(self):
        source = module_fixture()
        valid = ModuleEdit(152, source[152:156], bytes(4))
        for edits in ((), (valid, valid), (ModuleEdit(152, bytes(4), bytes(4)),),
                      (ModuleEdit(280, source[280:284], bytes(4)),),
                      (ModuleEdit(152, source[152:156], bytes(4), (Fixup(4, 4, "target"),)),),
                      (ModuleEdit(152, source[152:156], bytes(4), (Fixup(0, 4, "missing"),)),)):
            with self.subTest(edits=edits), self.assertRaises(InvalidModule):
                compile_module(source, edits)

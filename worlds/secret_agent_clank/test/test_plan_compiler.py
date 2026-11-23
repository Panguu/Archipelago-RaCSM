import struct
import unittest

from ..core.patches.asm import Patch
from ..core.patches.plan_compiler import compile_native_plan
from ..core.patches.snr2 import InvalidModule, SNR2Module
from .test_snr2 import module_fixture


def builder(base, loaded, exports):
    target = base + 200
    replacement = struct.pack("<6I", target, 0x0C000000 | ((base + 192) >> 2),
                              0x3C020000 | ((target + 0x8000) >> 16), 0x24420000 | (target & 65535),
                              0x3C030000 | (target >> 16), 0x34630000 | (target & 65535))
    return [Patch(base + 160, loaded[160:184], replacement)]


class TestPlanCompiler(unittest.TestCase):
    def test_pointer_jump_signed_and_unsigned_pairs(self):
        data = module_fixture()
        imports = {"import": 0x123450}
        compiled = SNR2Module(compile_native_plan(data, imports, builder))
        for base in (0x328B00, 0x407F30, 0x407F40, 0x40FF30, 0x40FF40, 0x908000):
            loaded, exports = SNR2Module(data).relocate(base, imports)
            expected = builder(base, loaded, exports)[0]
            actual, _ = compiled.relocate(base, imports)
            self.assertEqual(actual[160:184], expected.replacement)

    def test_address_dependent_layout_rejected(self):
        def changed(base, loaded, exports):
            offset = 160 if base == 0x400000 else 164
            return [Patch(base + offset, loaded[offset:offset + 4], bytes(4))]
        with self.assertRaisesRegex(InvalidModule, "layout"):
            compile_native_plan(module_fixture(), {"import": 0x123450}, changed)

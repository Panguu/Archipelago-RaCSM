import unittest

from ..core.patches.bindings import BindingCompiler, decode_binding
from ..core.patches.snr2 import SNR2Module
from .test_snr2 import module_fixture


class TestBindings(unittest.TestCase):
    def test_code_templates_match_native_relocations(self):
        data = module_fixture()
        imports = {"import": 0x123450}
        compiler = BindingCompiler(data, imports, 0x400000)
        recipe = compiler.code(0x400080, 28)
        for base in (0x328B00, 0x408010, 0x508010, 0x918000):
            loaded, _ = SNR2Module(data).relocate(base, imports)
            self.assertEqual(decode_binding(recipe, base), loaded[128:156])

    def test_data_bindings_preserve_keys_and_rebase_addresses(self):
        compiler = BindingCompiler(module_fixture(), {"import": 0x123450}, 0x400000)
        recipe = compiler.value({"slots": {3: "weapon"}, "addresses": (0x400080, 0x206328), "set": {1, 3}})
        self.assertEqual(decode_binding(recipe, 0x508000),
                         {"slots": {3: "weapon"}, "addresses": (0x508080, 0x206328), "set": {1, 3}})

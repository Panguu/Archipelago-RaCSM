import unittest

from ..core.patches.asm import jump, packed, Patch
from ..core.patches.module_arena import ModuleArena, reserve_arena
from ..core.patches.module_compiler import ModuleEdit, compile_module
from ..core.patches.plan_compiler import compile_native_plan
from ..core.patches.snr2 import InvalidModule, SNR2Module, word
from .test_snr2 import module_fixture


class TestModuleArena(unittest.TestCase):
    def test_relocated_jump_into_new_code(self):
        source, start = reserve_arena(module_fixture(), 128)

        def build(base, loaded, exports):
            arena = ModuleArena(base, loaded, start)
            address = arena.allocate(packed([jump(exports["target"]), 0]))
            return [Patch(base + 152, loaded[152:156], packed([jump(address, True)])), *arena.patches]

        compiled = compile_native_plan(source, {"import": 0x123450}, build, arena_start=start)
        for base in (0x328B00, 0x408010, 0x908000):
            loaded, _ = SNR2Module(compiled).relocate(base, {"import": 0x123450})
            self.assertEqual(word(loaded, 152), jump(base + start, True))
            self.assertEqual(word(loaded, start), jump(base + 192))

    def test_metadata_cannot_be_declared_as_arena(self):
        source, _ = reserve_arena(module_fixture(), 128)
        edit = ModuleEdit(280, source[280:284], bytes(4))
        for start in (128, 256, 320, 400, 513, len(source)):
            with self.subTest(start=start), self.assertRaises(InvalidModule):
                compile_module(source, (edit,), arena_start=start)

    def test_arena_exhaustion_is_transactional(self):
        source, start = reserve_arena(module_fixture(), 16)
        arena = ModuleArena(0x400000, source, start)
        with self.assertRaises(InvalidModule):
            arena.allocate(bytes(17))
        self.assertEqual(arena.cursor, start)
        self.assertEqual(arena.patches, [])

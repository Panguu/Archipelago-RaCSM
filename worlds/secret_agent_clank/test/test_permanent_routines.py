import unittest

from ..core.patches.asm import packed
from ..core.patches.progression import Progression
from ..core.patches.module_arena import ModuleArena
from ..core.patches.vendor_icon import prepare_vendor_icon
from ..core.patches.frontend_build import prepare_frontend, RETAIL_BASE
from ..core.patches.starting_case import StartingCase
from ..core.patches.asm import jump
from .mips_cpu import CPU
from .test_runtime import Memory


class TestPermanentRoutines(unittest.TestCase):
    def test_frontend_starting_case_changes_only_config_data(self):
        base = 0x400000
        rebase = lambda address: base + address - RETAIL_BASE
        data = bytearray(0x110000)
        init, change = rebase(StartingCase.INIT), rebase(StartingCase.CHANGE_LEVEL)
        for site in StartingCase.CALLS:
            offset = rebase(site) - base
            data[offset:offset + 8] = packed([jump(init, True), 0x24050001])
        for site in StartingCase.TRAVEL_CALLS:
            offset = rebase(site) - base - 4
            data[offset:offset + 12] = packed([0x24040001, jump(change, True), 0x24050001])
        patches, config = prepare_frontend(base, bytes(data), 0x100000)
        memory = Memory()
        memory.data = bytearray(0x2000000)
        memory.write_int8 = lambda address, value: memory.batch_write_int8([(address, value)])
        memory.write_bytes(base, bytes(data))
        for patch in patches:
            memory.write_bytes(patch.address, patch.replacement)
        save = 0x200000
        memory.write_int32(rebase(0x418FD8), save)
        for module, clank, qwark in ((1, 0, 0), (4, 1, 0), (11, 0, 1)):
            memory.write_bytes(config, packed([module, clank, qwark]))
            for site in StartingCase.CALLS:
                cpu = CPU(memory)
                cpu.r[4] = save
                cpu.run(rebase(site), stop=rebase(site) + 8, stubs={init: lambda cpu: None})
                self.assertEqual(memory.read_int32(save + 0xECC), module)
                self.assertEqual(memory.read_int8(save + 0x589), clank)
                self.assertEqual(memory.read_int8(save + 0x5A8), qwark)
                self.assertEqual(memory.read_int8(save + 0x5AA), 1)
            for site in StartingCase.TRAVEL_CALLS:
                cpu = CPU(memory)
                cpu.run(rebase(site) - 4, stop=rebase(site) + 8, stubs={change: lambda cpu: None})
                self.assertEqual(cpu.r[4], module)
                self.assertEqual(cpu.r[5], 1)
                self.assertEqual(memory.read_int32(save + 0xECC), module)

    def test_gain_settings_change_without_code_writes(self):
        memory = Memory()
        original = packed([0x27BDFFF0, 0xFFB00000])
        code = Progression.gain_wrapper(0x120000, original, 0x138000)
        memory.write_bytes(0x110000, code)
        for multiplier in (1, 2, 3, 10):
            memory.write_int32(0x138000, multiplier)
            for value in (-100, 0, 7, 12345):
                cpu = CPU(memory)
                cpu.r[29], cpu.r[16], cpu.r[4] = 0x700000, 99, value & 0xFFFFFFFF
                cpu.run(0x110000, stop=0x120008)
                self.assertEqual(cpu.r[4], (value * multiplier if value > 0 else value) & 0xFFFFFFFF)
                self.assertEqual(cpu.r[29], 0x6FFFF0)
                self.assertEqual(memory.read_int32(0x6FFFF0), 99)
                self.assertEqual(memory.read_bytes(0x110000, len(code)), code)

    def test_weapon_gain_preserves_both_native_paths(self):
        memory = Memory()
        code = Progression.weapon_gain_wrapper(0x120000, 0x138000)
        memory.write_bytes(0x110000, code)
        memory.write_int32(0x140064, 777)
        for multiplier in (1, 2, 3, 10):
            memory.write_int32(0x138000, multiplier)
            for branch in (0, 1):
                cpu = CPU(memory)
                cpu.r[18], cpu.r[20], cpu.r[21] = 123, 0x140000, branch
                cpu.run(0x110000, stop=0x12011C if branch else 0x12010C)
                self.assertEqual(cpu.r[18], 123 * multiplier)
                self.assertEqual(cpu.r[4], 777)
                self.assertEqual(cpu.r[31], CPU.STOP)

    def test_vendor_icon_copies_once_and_preserves_other_icons(self):
        memory = Memory()
        lookup, invalidate, table, cache = 0x110000, 0x110100, 0x130000, 0x140000
        memory.write_bytes(lookup, packed([0x3C030013, 0x000420C0, 0x24630000,
                                          0x00641821, 0x03E00008, 0x8C620004]))
        memory.write_bytes(invalidate, packed([0x3C020014, 0x03E00008, 0xAC400000]))
        texture, image = 0x150000, 0x160000
        retail_pixels = bytes(range(256)) * 8
        memory.write_bytes(image, retail_pixels)
        memory.write_int32(0x17000C, 8)
        memory.write_int32(table + 73 * 8 + 4, texture)
        memory.write_int32(table + 12, 123456)
        for address, value in ((texture + 0x34, 0x00200020), (texture + 0x58, image),
                               (texture + 0x98, image + 1024), (cache, 99)):
            memory.write_int32(address, value)
        arena = ModuleArena(0x200000, bytes(8192), 128)
        patches = prepare_vendor_icon(memory, {"GetIconTextureID__14DrawObjManagerUi": lookup,
                                               "aglPs2VramInvalidate__Fv": invalidate,
                                               "g_PauseModeData": 0x170000}, arena)
        for patch in patches + arena.patches:
            memory.write_bytes(patch.address, patch.replacement)
        cpu = CPU(memory)
        cpu.r[4] = 73
        cpu.run(lookup, max_steps=10000)
        self.assertEqual(cpu.r[2], texture)
        self.assertEqual(memory.read_bytes(image, 2048), arena.patches[0].replacement)
        self.assertEqual(memory.read_int32(cache), 0)
        memory.write_int32(cache, 42)
        cpu = CPU(memory)
        cpu.r[4] = 73
        cpu.run(lookup)
        self.assertEqual(memory.read_int32(cache), 42)
        cpu = CPU(memory)
        cpu.r[4] = 1
        cpu.run(lookup)
        self.assertEqual(cpu.r[2], 123456)
        memory.write_int32(0x17000C, 0)
        cpu = CPU(memory)
        cpu.r[4] = 73
        cpu.run(lookup, max_steps=5000)
        self.assertEqual(memory.read_bytes(image, 2048), retail_pixels)
        memory.write_int32(0x17000C, 16)
        cpu = CPU(memory)
        cpu.r[4] = 73
        cpu.run(lookup, max_steps=5000)
        self.assertEqual(memory.read_bytes(image, 2048), arena.patches[0].replacement)

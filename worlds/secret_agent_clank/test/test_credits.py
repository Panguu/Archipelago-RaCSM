import os
from pathlib import Path
import unittest

from ..core.patches import credits
from ..core.patches.module_arena import ModuleArena, reserve_arena
from ..core.patches.plan_compiler import compile_native_plan
from ..core.patches.snr2 import SNR2Module, resident_exports, word
from ..patcher.filenames import EXECUTABLE, LEVEL_FILES
from ..patcher.iso import ISOImage
from .mips_cpu import CPU
from .test_runtime import Memory


@unittest.skipUnless(os.environ.get("SAC_TEST_ISO"), "Set SAC_TEST_ISO for native credits tests")
class TestInteractiveCredits(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with Path(os.environ["SAC_TEST_ISO"]).open("rb") as stream:
            iso = ISOImage(stream)
            cls.source = iso.read_file(LEVEL_FILES[32])
            cls.imports = resident_exports(iso.read_file(EXECUTABLE))
        cls.expanded, cls.start = reserve_arena(cls.source)

        def build(base, loaded, symbols):
            arena = ModuleArena(base, loaded, cls.start)
            return [*credits.prepare_credits(base, loaded, symbols, arena), *arena.patches]

        if os.environ.get("SAC_TEST_BUILD"):
            cls.compiled = Path(os.environ["SAC_TEST_BUILD"], "module-32.rel").read_bytes()
        else:
            cls.compiled = compile_native_plan(cls.expanded, cls.imports, build, arena_start=cls.start)

    def test_native_setup_initializes_every_entry_and_selector_uses_same_table(self):
        for base in (0x328B00, 0x508010, 0x617FF0):
            with self.subTest(base=base):
                loaded, _ = SNR2Module(self.compiled).relocate(base, self.imports)
                memory = Memory()
                memory.data = bytearray(0x2000000)
                memory.write_int8 = lambda address, value: memory.write_bytes(address, bytes([value]))
                memory.write_bytes(base, loaded)
                low = word(loaded, 0xBB444) & 65535
                target = ((word(loaded, 0xBB43C) & 65535) << 16) + (low - 65536 if low & 32768 else low)
                self.assertGreaterEqual(target, base + self.start)
                size = credits.RETAIL_COUNT * credits.ENTRY_SIZE
                retail = self.source[credits.TABLE_OFFSET:credits.TABLE_OFFSET + size]
                self.assertEqual(memory.read_bytes(target, size), retail)
                cpu = CPU(memory)
                strlen = (word(loaded, 0xBB450) & 0x3FFFFFF) << 2

                def length(machine):
                    machine.r[2] = memory.read_bytes(machine.r[4], 64).index(0)

                end = target + (credits.RETAIL_COUNT + len(credits.LINES)) * 64
                sentinel = memory.read_bytes(end, 64)
                cpu.run(base + 0xBB43C, stop=base + 0xBB4D0,
                        stubs={strlen: length}, max_steps=200000)
                self.assertEqual(len(cpu.calls), credits.RETAIL_COUNT + len(credits.LINES))
                self.assertEqual(memory.read_bytes(end, 64), sentinel)
                for i, line in enumerate(credits.LINES, credits.RETAIL_COUNT):
                    self.assertEqual(memory.read_bytes(target + i * 64, 64).split(b"\0")[0],
                                     line.upper().encode("ascii"))
                selector = CPU(memory)
                selector.run(base + 0xBB598, stop=base + 0xBB5A0)
                self.assertEqual(selector.r[4], target)
                count = word(loaded, 0xBB590) & 65535
                self.assertEqual(count, credits.RETAIL_COUNT + len(credits.LINES))
                # Execute the real selector, including DIVU/MFHI and its two
                # writes to the persistent index, through the full wrap.
                index_address = base + 0x21EA18
                memory.write_int32(index_address, 0xFFFFFFFF)
                visited = []
                for expected in [*range(count), 0]:
                    selector.run(base + 0xBB58C, stop=base + 0xBB5D0)
                    self.assertEqual(memory.read_int32(index_address), expected)
                    self.assertEqual(selector.r[4], target + expected * 64)
                    visited.append(memory.read_bytes(selector.r[4], 64).split(b"\0")[0])
                self.assertEqual(visited[113:count], [line.upper().encode('ascii') for line in credits.LINES])
                self.assertEqual(memory.read_bytes(base + credits.TABLE_OFFSET, size), retail)

    def test_authored_end_event_schedules_extra_waves_before_movie(self):
        for base in (0x328B00, 0x617FF0):
            with self.subTest(base=base):
                loaded, _ = SNR2Module(self.compiled).relocate(base, self.imports)
                memory = Memory()
                memory.data = bytearray(0x2000000)
                memory.write_bytes(base, loaded)
                capture = (word(loaded, 0xBB4F0) & 0x3FFFFFF) << 2
                self.assertEqual(word(loaded, 0xBB4F0) >> 26, 2)
                state = ((memory.read_int32(capture) & 65535) << 16) | (memory.read_int32(capture + 4) & 65535)
                cpu = CPU(memory)
                cpu.r[4], cpu.r[5], cpu.r[21] = 0x123000, 7, 0xABCDEF
                cpu.run(base + 0xBB4F0, stop=base + 0xBB4F8)
                self.assertEqual(memory.read_int32(state), 0x123000)
                self.assertEqual(memory.read_int32(state + 4), 7)
                self.assertEqual(memory.read_int32(cpu.r[29] + 0xE8), 0xABCDEF)
                index = base + 0x21EA18
                for previous, config in ((109, 0x124000), (110, 0x125000), (111, 0x126000)):
                    memory.write_int32(index, previous)
                    cpu = CPU(memory)
                    cpu.r[4], cpu.r[5] = config, 7
                    cpu.run(base + 0xBB4F0, stop=base + 0xBB4F8)
                self.assertEqual(memory.read_int32(state), 0x124000)
                self.assertEqual(memory.read_int32(state + 16), 0x125000)
                memory.write_int32(index, 112)
                begin = (word(loaded, 0xBBC28) & 0x3FFFFFF) << 2
                tick = (word(loaded, 0xBDF2C) & 0x3FFFFFF) << 2
                CPU(memory).run(begin)
                emitted, completed = [], []
                frame = 0

                def wave(machine):
                    row = memory.read_int32(index) + 1 - credits.RETAIL_COUNT
                    config = 0x125000 if row in credits.SUBTITLE_ROWS else 0x124000
                    self.assertEqual((machine.r[4], machine.r[5]), (config, 7))
                    # Use the actual selector; only particle rendering is stubbed.
                    selector = CPU(memory)
                    selector.run(base + 0xBB58C, stop=base + 0xBB5D0)
                    emitted.append((frame, memory.read_int32(index)))

                def complete(machine):
                    completed.append(frame)

                stubs = {base + 0xBB4F0: wave, base + 0xBA650: complete,
                         base + 0xBAA18: lambda machine: None}
                for frame in range((credits.LINE_TICKS + 1) * 13):
                    cpu = CPU(memory)
                    cpu.r[16] = 0xDEADBEEF
                    cpu.run(tick, stubs=stubs)
                    self.assertEqual(cpu.r[16], 0xDEADBEEF)
                    self.assertEqual(cpu.r[29], 0x1FF0000)
                self.assertEqual([i for _, i in emitted], list(range(113, 113 + len(credits.LINES))))
                for row in credits.SUBTITLE_ROWS:
                    self.assertEqual(emitted[row][0] - emitted[row - 1][0], 1)
                self.assertIn('Pangu    Amondo', credits.LINES)
                self.assertTrue(all('"' not in line for line in credits.LINES))
                self.assertEqual(credits.LINES[3].strip(), 'Trap')
                self.assertEqual(len(completed), 1)
                self.assertGreaterEqual(completed[0] - emitted[-1][0], credits.LINE_TICKS)
                self.assertEqual(memory.read_int32(state + 8), 0)
                memory.write_bytes(state, bytes([255]) * 20)
                CPU(memory).run(base + 0xBD8F8, stop=base + 0xBD900)
                self.assertEqual(memory.read_bytes(state, 20), bytes(20))

    def test_changed_native_instruction_is_rejected(self):
        base = 0x400000
        loaded, symbols = SNR2Module(self.expanded).relocate(base, self.imports)
        damaged = bytearray(loaded)
        damaged[0xBB590] ^= 1
        arena = ModuleArena(base, damaged, self.start)
        with self.assertRaisesRegex(ValueError, "instruction differs"):
            credits.prepare_credits(base, damaged, symbols, arena)

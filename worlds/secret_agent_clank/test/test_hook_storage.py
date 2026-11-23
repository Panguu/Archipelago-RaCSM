import unittest

from ..core.patches import Patch, Progression, free_blocks, storage_address
from .mips_cpu import CPU
from .test_native_capture_plans import CaptureMemory


class HookStorageTests(unittest.TestCase):
    def test_split_manual_guard_rejects_invalid_slots_without_touching_stack(self):
        p = CaptureMemory()
        def allocate(code):
            p.write_bytes(0x160000, code)
            return 0x160000
        code = Progression.manual_xp_guard(0x100000, 0x120000, 0x150000, allocate)
        p.write_bytes(0x140000, code)
        for slot in (40, 255, 0xFFFFFFFF):
            cpu = CPU(p)
            cpu.r[4:7] = [slot, 50, 1]
            stack = cpu.r[29]
            cpu.run(0x140000)
            self.assertEqual(cpu.r[4:7], [slot, 50, 1])
            self.assertEqual(cpu.r[29], stack)
            self.assertEqual(cpu.r[2], 0)

    def test_small_hooks_preserve_room_for_cap_table(self):
        ranges = [(0x1000, 0x102C), (0x2000, 0x2024)]
        address = storage_address(ranges, [], 28)
        self.assertEqual(address, 0x2000)
        patches = [Patch(address, bytes(28), bytes(28))]
        self.assertEqual(storage_address(ranges, patches, 40), 0x1000)

    def test_alignment_and_overlapping_occupied_spans(self):
        patches = [Patch(0x1008, bytes(12), bytes(12)),
                   Patch(0x1010, bytes(12), bytes(12))]
        self.assertEqual(free_blocks([(0x1001, 0x1028)], patches),
                         [(0x1004, 0x1008), (0x101C, 0x1028)])
        self.assertEqual(storage_address([(0x1001, 0x1028)], patches, 12), 0x101C)
        self.assertIsNone(storage_address([(0x1001, 0x1028)], patches, 16))

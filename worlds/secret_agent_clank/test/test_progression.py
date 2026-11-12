import struct
import unittest
from types import SimpleNamespace

from ..constants import PROGRESSIVE_TO_INTERNAL, WEAPON_ORDER, ProgressiveWeaponsOptions
from ..core.patches import Progression
from .mips_cpu import CPU
from .test_native_capture_plans import CaptureMemory
from .test_runtime import Memory
from ..core.patches.asm import packed


class ProgressionTests(unittest.TestCase):
    def replay_fixture(self):
        p = CaptureMemory()
        arena, moby = 0x110000, 0x120000
        p.write_bytes(arena + 0x98, packed([
            0x3C013F80, 0x4481A000, 0x10400003, 0x8E440000,
            0x3C013E80, 0x4481A000]))
        p.write_bytes(moby + 0x188, packed([
            0x14400005, 0, 0x3C013E80, 0x44810000,
            0, 0x4600A502, 0x4600A024, 0x44080000]))
        symbols = {"Arena_PreCalcXPForChallenge__FP4Moby": arena,
                   "MOBY_ComputeWeaponXP__FPC4MobyRC10DamageInfo": moby}
        return p, symbols, arena, moby

    def test_repeat_xp_matches_first_clear_and_preserves_multiplier(self):
        # A new module image on each visit must receive the same edits.
        for visit in range(2):
            p, symbols, arena, moby = self.replay_fixture()
            for patch in Progression(p).replay_xp_patches(symbols):
                p.write_bytes(patch.address, patch.replacement)
            for wins in (0, 1, 2, 20):
                cpu = CPU(p)
                cpu.r[2] = wins
                cpu.run(arena + 0x98, stop=arena + 0xB0)
                self.assertEqual(cpu.float(20), 1.0, (visit, wins))
            for first_kill in (0, 1):
                cpu = CPU(p)
                cpu.r[2] = first_kill
                cpu.set_float(20, 100.0)
                cpu.run(moby + 0x188, stop=moby + 0x1A0)
                self.assertEqual(cpu.float(20), 100.0)
                for multiplier in (1, 5, 10):
                    p.write_bytes(0x130000, Progression.weapon_gain_wrapper(0x140000, multiplier))
                    cpu.r[18], cpu.r[20], cpu.r[21] = int(cpu.float(20)), 0x150000, 1
                    cpu.run(0x130000, stop=0x14011C)
                    self.assertEqual(cpu.r[18], 100 * multiplier)

    def test_repeat_xp_rejects_changed_native_code_without_writes(self):
        for offset, label in ((0x110098, "Arena"), (0x120188, "Enemy")):
            p, symbols, _, _ = self.replay_fixture()
            p.data[offset] ^= 1
            before = bytes(p.data)
            with self.assertRaisesRegex(RuntimeError, label + " repeat XP layout changed"):
                Progression(p).replay_xp_patches(symbols)
            self.assertEqual(bytes(p.data), before)

    def test_weapon_multiplier_scales_capped_award_and_preserves_level_up_path(self):
        for multiplier in range(2, 11):
            for award in (0, 1, 100):
                for allow_level_up in (0, 1):
                    with self.subTest(multiplier=multiplier, award=award, allow_level_up=allow_level_up):
                        p = CaptureMemory()
                        p.write_bytes(0x110000, Progression.weapon_gain_wrapper(0x120000, multiplier))
                        p.write_int32(0x130064, 777)
                        cpu = CPU(p)
                        cpu.r[18], cpu.r[20], cpu.r[21] = award, 0x130000, allow_level_up
                        cpu.run(0x110000, stop=0x12011C if allow_level_up else 0x12010C)
                        self.assertEqual(cpu.r[18], award * multiplier)
                        self.assertEqual(cpu.r[4], 777)
                        self.assertEqual(cpu.r[20:22], [0x130000, allow_level_up])
                        self.assertEqual(cpu.r[31], CPU.STOP)

    def test_compact_gain_wrapper_replays_prologue_in_jump_delay_slot(self):
        for register in (4, 5):
            for value in (-100, 0, 1, 12345):
                for second in (0xFFB00000, 0x3C020050):
                    p = CaptureMemory()
                    original = struct.pack("<2I", 0x27BDFFF0, second)
                    p.write_bytes(0x110000, Progression.gain_wrapper(0x120000, original, register, 4))
                    cpu = CPU(p)
                    cpu.r[29], cpu.r[16], cpu.r[register] = 0x700000, 123, value & 0xFFFFFFFF
                    cpu.run(0x110000, stop=0x120008)
                    self.assertEqual(cpu.r[register], (value * 4 if value > 0 else value) & 0xFFFFFFFF)
                    self.assertEqual(cpu.r[29], 0x6FFFF0)
                    self.assertEqual(cpu.r[31], CPU.STOP)
                    if second == 0xFFB00000:
                        self.assertEqual(p.read_int32(0x6FFFF0), 123)
                    else:
                        self.assertEqual(cpu.r[2], 0x500000)

    def loader_fixture(self):
        mem = Memory()
        pr = Progression(mem)
        replay, pointer = 0x110000, 0x208000
        for offset, word in enumerate((0x3C020021, 0x8C448000, 0x8C830ED4, 0x0003182B)):
            mem.batch_write_int32([(replay + 0x1C + offset * 4, word)])
        symbols = {"GADGET_g_GadgetList": 0x100000, "GLOBALVARS_IsInReplayMode__Fv": replay}
        self.assertEqual(pr.prepare(symbols, SimpleNamespace(patches=[]), 1, vendor_enabled=False), [])
        self.assertEqual(pr.save_pointer_address, pointer)
        self.assertIsNone(pr.ng_address)
        mem.batch_write_int32([(0x206328, 1), (0x206324, 0xFFFFFFFF), (0x206338, 3)])
        mem.writes.clear()
        return mem, pr, pointer

    def test_null_save_at_loader_gate_retries_after_initialization(self):
        mem, pr, pointer = self.loader_fixture()
        pr.sync()
        self.assertEqual(mem.writes, [])
        mem.batch_write_int32([(pointer, 0x300000), (0x300ED4, 2)])
        pr.sync()
        self.assertEqual(pr.ng_address, 0x300ED4)
        self.assertEqual(mem.read_int32(0x300ED4), 0)

    def test_save_relocation_never_reuses_previous_address(self):
        mem, pr, pointer = self.loader_fixture()
        mem.batch_write_int32([(pointer, 0x300000)])
        pr.sync()
        mem.batch_write_int32([(pointer, 0), (0x300ED4, 2)])
        pr.sync()
        self.assertIsNone(pr.ng_address)
        self.assertEqual(mem.read_int32(0x300ED4), 2)
        mem.batch_write_int32([(pointer, 0x400000), (0x400ED4, 1)])
        pr.sync()
        self.assertEqual(mem.read_int32(0x400ED4), 0)
        self.assertEqual(mem.read_int32(0x300ED4), 2)

    def test_transition_and_corrupt_pointer_cannot_write(self):
        mem, pr, pointer = self.loader_fixture()
        mem.batch_write_int32([(pointer, 0xFFFFFFFF), (0x206338, 0)])
        mem.writes.clear()
        pr.sync()
        self.assertEqual(mem.writes, [])
        mem.batch_write_int32([(0x206338, 3)])
        mem.writes.clear()
        with self.assertRaisesRegex(RuntimeError, "0xFFFFFFFF"):
            pr.sync()
        self.assertEqual(mem.writes, [])

    def test_caps_ownership_and_duplicate_replay(self):
        p = Progression(Memory())
        for ng in (0, 1, 2):
            p.configure({"progressive_weapons": ProgressiveWeaponsOptions.AUTOMATIC, "ng_plus": ng})
            p.receive([])
            self.assertFalse(any(p.ownership().values()))
            for name, internal in PROGRESSIVE_TO_INTERNAL.items():
                p.receive([name])
                self.assertEqual(p.levels[internal], 1)
                self.assertTrue(p.ownership()[internal])
                p.receive([name] * 12)
                expected = 4 if ng == 0 or internal == "ryno" else 8
                self.assertEqual(p.levels[internal], expected)
                p.receive([name] * 12)
                self.assertEqual(p.levels[internal], expected)

    def test_disabled_preserves_combat_level_and_xp(self):
        mem = Memory()
        p = Progression(mem)
        p.base = 0x100000
        p.receive(list(PROGRESSIVE_TO_INTERNAL))
        p.sync()
        self.assertEqual(mem.writes, [])
        self.assertEqual(p.ownership(), {})

    def test_native_zero_based_level_and_xp_reset(self):
        mem = Memory()
        p = Progression(mem)
        p.configure({"progressive_weapons": ProgressiveWeaponsOptions.AUTOMATIC, "ng_plus": 1})
        name = next(n for n, i in PROGRESSIVE_TO_INTERNAL.items() if i == "blaster")
        p.receive([name] * 5)
        p.base = 0x100000
        slot = p.base + WEAPON_ORDER.index("blaster") * 0x74
        mem.batch_write_int32([(slot + 0x64, 123)])
        p.sync()
        self.assertEqual(mem.read_int32(slot + 0x5C), 4)
        self.assertEqual(mem.read_int32(slot + 0x64), 0)
        mem.writes.clear()
        p.sync()
        self.assertEqual(mem.writes, [])

    def test_multiplier_bounds(self):
        for key in ("weapon_xp_multiplier", "health_xp_multiplier", "bolt_multiplier"):
            for value in (0, 11):
                with self.assertRaises(ValueError):
                    Progression(Memory()).configure({key: value})

    def test_emitted_gain_instructions_preserve_deductions(self):
        original = struct.pack("<2I", 0x27BDFFF0, 0xFFB00000)
        for reg in (4, 5):
            for value in (-100, 0, 1, 12345):
                code = struct.unpack("<7I", Progression.gain_wrapper(0x200000, original, reg, 10))
                regs = [0] * 32
                regs[reg] = value
                pc = 0
                lo = 0
                while pc < 4:
                    word = code[pc]
                    op, rs, rt = word >> 26, (word >> 21) & 31, (word >> 16) & 31
                    if op == 6:
                        delay = code[pc + 1]
                        self.assertEqual(delay >> 26, 9)
                        regs[(delay >> 16) & 31] = delay & 65535
                        pc = pc + 1 + (word & 65535) if regs[rs] <= 0 else pc + 2
                    elif op == 0 and word & 63 == 24:
                        lo = regs[rs] * regs[rt]
                        pc += 1
                    elif op == 0 and word & 63 == 18:
                        regs[(word >> 11) & 31] = lo
                        pc += 1
                    else:
                        self.fail(hex(word))
                self.assertEqual(pc, 4)
                self.assertEqual(regs[reg], value * 10 if value > 0 else value)
                self.assertEqual(struct.pack("<2I", code[4], code[6]), original)
                self.assertEqual((code[5] & 0x3FFFFFF) << 2, 0x200008)

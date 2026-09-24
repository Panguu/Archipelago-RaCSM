import struct
import unittest
from types import SimpleNamespace

from ..constants.weapon_progression import PROGRESSIVE_TO_INTERNAL
from ..core.inventories.weapons import WEAPON_ORDER
from ..core.patches.progression import Progression
from .test_runtime import Memory


class ProgressionTests(unittest.TestCase):
    def loader_fixture(self):
        mem = Memory()
        pr = Progression(mem)
        replay, pointer = 0x110000, 0x208000
        for offset, word in enumerate((0x3C020021, 0x8C448000, 0x8C830ED4, 0x0003182B)):
            mem.batch_write_int32([(replay + 0x1C + offset * 4, word)])
        symbols = {"GADGET_g_GadgetList": 0x100000, "GLOBALVARS_IsInReplayMode__Fv": replay}
        # A relocated module has a valid code signature but a null save pointer.
        self.assertEqual(pr.prepare(symbols, SimpleNamespace(patches=[]), 1), [])
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
            p.configure({"progressive_weapons": True, "ng_plus": ng})
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
        p.configure({"progressive_weapons": True, "ng_plus": 1})
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
        # Execute the arithmetic prefix, including the branch delay slot;
        # ensure both paths resume the untouched prologue and target+8.
        original = struct.pack("<2I", 0x27BDFFF0, 0xFFB00000)
        for reg in (4, 5):
            for value in (-100, 0, 1, 12345):
                code = struct.unpack("<8I", Progression.gain_wrapper(0x200000, original, reg, 10))
                regs = [0] * 32
                regs[reg] = value
                pc = 0
                lo = 0
                while pc < 4:
                    word = code[pc]
                    op, rs, rt = word >> 26, (word >> 21) & 31, (word >> 16) & 31
                    if op == 6:  # blez; execute addiu delay slot
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
                self.assertEqual(struct.pack("<2I", *code[4:6]), original)
                self.assertEqual((code[6] & 0x3FFFFFF) << 2, 0x200008)
                self.assertEqual(code[7], 0)

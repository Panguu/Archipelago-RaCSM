import unittest

from ..constants.weapon_progression import TITAN_LOCATIONS
from ..core.inventories.weapons import WEAPON_ORDER
from ..core.patches import LocationHooks, jump
from ..core.patches.progression import Progression
from ..core.patches.titan_vendor import TitanVendor
from .test_runtime import Memory


class TitanTests(unittest.TestCase):
    def plan(self, checked=()):
        p = Memory()
        buy, builder = 0x100000, 0x200000
        symbols = {"SCRNVENDOR_ProcessPurchase__Fv": buy,
                   "GADGET_SetPowerLevel__FUiUib": 0x300000,
                   "GADGET_GetDefAtLevel__FUiUi": 0x300100}
        p.batch_write_int32([(buy + 0x168, 0x8E440010), (buy + 0x178, 0x8E05005C),
            (buy + 0x184, jump(0x300000, True)), (buy + 0x188, 0x24A50001),
            (buy + 0x338, jump(builder, True))])
        for offset in (0x63C, 0x6D8):
            for delta, word in ((-16, 0x0040802D), (-8, 0x0240202D), (-4, 0x0040882D),
                                (0, 0x8E02005C), (4, 0x54540013), (8, 0x26520001)):
                p.batch_write_int32([(builder + offset + delta, word)])
        h = LocationHooks(p)
        edits = TitanVendor(p).prepare(symbols, h, checked)
        p.write_bytes = lambda address, data: p.data.__setitem__(slice(address, address + len(data)), data)
        h.patches = edits
        h.reported = set(checked)
        h._install_plan()
        return p, h

    def execute(self, p, start, regs):
        pc = start
        pending = None
        for _ in range(30):
            w = p.read_int32(pc)
            op, rs, rt = w >> 26, (w >> 21) & 31, (w >> 16) & 31
            imm = w & 65535
            previous = pending
            pending = None
            if not w: pass
            elif op == 15: regs[rt] = imm << 16
            elif op == 13: regs[rt] = regs[rs] | imm
            elif op == 0 and w & 63 == 33: regs[(w >> 11) & 31] = regs[rs] + regs[rt]
            elif op == 36: regs[rt] = p.read_int8(regs[rs] + imm)
            elif op == 35: regs[rt] = p.read_int32(regs[rs] + imm)
            elif op == 40: p.batch_write_int8([(regs[rs] + imm, regs[rt])])
            elif op == 9: regs[rt] = regs[rs] + imm
            elif op == 4:
                pending = pc + 4 + 4 * imm if regs[rs] == regs[rt] else pc + 8
            elif op == 2: pending = (w & 0x3FFFFFF) << 2
            elif op == 0 and w & 63 == 8: pending = regs[rs]
            else: self.fail(hex(w))
            pc = previous if previous is not None else pc + 4
            if previous is not None and not start <= pc < start + 56:
                return pc
        self.fail("Routine did not return")

    def test_offer_and_record_are_independent_of_gameplay_level(self):
        for flag in (0, 2, 3, 4):
            p, h = self.plan()
            table = h.tables["titan"]
            p.batch_write_int8([(table + 2, flag)])
            p.batch_write_int32([(0x40002C, 123), (0x40005C, 7)])
            regs = [0] * 32
            regs[17], regs[18], regs[20], regs[31] = 0x400000, 2, 3, 0x200644
            target = self.execute(p, 0x100164 + 28, regs)
            self.assertEqual(target, 0x20064C if flag == 3 else 0x20068C)
            if flag == 3: self.assertEqual(regs[5], 123)
            regs = [0] * 32
            regs[4] = 2
            self.assertEqual(self.execute(p, 0x100164 + 80, regs), 0x100338)
            self.assertEqual(p.read_int8(table + 2), 2)
            self.assertEqual(p.read_int32(0x40005C), 7)

    def test_checked_offer_is_suppressed_and_ryno_excluded(self):
        p, h = self.plan({TITAN_LOCATIONS["blaster"]})
        self.assertEqual(p.read_int8(h.tables["titan"] + 2), 2)
        self.assertNotIn(10, h.locations["titan"])
        self.assertEqual(len(h.locations["titan"]), 14)

    def test_nonprogressive_titan_bridge_only_at_owned_v4_in_ng_plus(self):
        for ng in (0, 1, 2):
            for progressive in (False, True):
                for owned in (0, 1):
                    for native in range(8):
                        p = Memory()
                        pr = Progression(p)
                        pr.configure({"ng_plus": ng, "progressive_weapons": progressive})
                        pr.base = 0x100000
                        level = pr.base + WEAPON_ORDER.index("blaster") * 0x74 + 0x5C
                        p.batch_write_int32([(level, native), (level + 8, 123), (level + 20, owned)])
                        pr.sync()
                        upgrade = ng > 0 and not progressive and owned and native == 3
                        self.assertEqual(p.read_int32(level), 4 if upgrade else native)
                        self.assertEqual(p.read_int32(level + 8), 0 if upgrade else 123)
                        self.assertEqual(pr.ownership(), {})

    def test_auto_titan_excludes_ryno_and_preserves_later_combat_levels(self):
        p = Memory()
        pr = Progression(p)
        pr.configure({"ng_plus": 1})
        pr.receive([])
        pr.base = 0x100000
        level = pr.base + WEAPON_ORDER.index("blaster") * 0x74 + 0x5C
        ryno = pr.base + WEAPON_ORDER.index("ryno") * 0x74 + 0x5C
        p.batch_write_int32([(level, 3), (level + 20, 1), (ryno, 3), (ryno + 20, 1)])
        pr.sync()
        self.assertEqual(p.read_int32(level), 4)
        self.assertEqual(p.read_int32(ryno), 3)
        p.batch_write_int32([(level, 7), (level + 8, 123)])
        pr.sync()
        self.assertEqual(p.read_int32(level), 7)
        self.assertEqual(p.read_int32(level + 8), 123)

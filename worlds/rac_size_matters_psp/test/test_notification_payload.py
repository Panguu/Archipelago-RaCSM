"""Run the overlay wrapper against synthetic MIPS registers and memory."""
import struct
import unittest
from ..core.patches.notification import Font, payload


class TestNotificationPayload(unittest.TestCase):
    def execute(self, remaining):
        entry, code, state, text = 0x09100000, 0x09900000, 0x09900200, 0x09900300
        font = Font(0x09110000, 0x09120000, 0x09400000, 0x09400004)
        raw = payload(code, state, text, entry, struct.pack('<2I', 0x27BDFFA0, 0x3C040940), font)
        self.assertLessEqual(len(raw), 256)
        memory = {code+i*4: word for i,word in enumerate(struct.unpack('<'+'I'*(len(raw)//4), raw))}
        colour = 0x09400008
        memory.update({state: remaining, font.colour_slot: colour, colour: 0x12345678,
                       font.scratch: 0xABCDEF01})
        regs = [0]+[i*32 for i in range(1, 32)]
        regs[29] = 0x09800000
        before = regs[:]
        pc, delayed, drawn = code, None, []
        def signed(value):
            return value if value < 0x80000000 else value-0x100000000
        for _ in range(150):
            if pc == entry+8:
                break
            if pc in (font.width, font.draw):
                if pc == font.width:
                    self.assertEqual(regs[4], text)
                else:
                    drawn.append((regs[4], regs[5], regs[6], memory[colour], memory[font.scratch]))
                returning = regs[31]
                for reg in (2,3,4,5,6,7,8,9,10,11,12,13,14,15,24,25):
                    regs[reg] = 0xDEADBEEF
                if pc == font.width:
                    regs[2] = 82
                pc = returning
                continue
            word = memory[pc]
            op, rs, rt, rd, imm = word>>26, (word>>21)&31, (word>>16)&31, (word>>11)&31, word&65535
            simm = (imm^32768)-32768
            old_delay, delayed = delayed, None
            if word == 0:
                pass
            elif op == 9:
                regs[rt] = (regs[rs]+simm)&0xFFFFFFFF
            elif op == 15:
                regs[rt] = imm<<16
            elif op == 13:
                regs[rt] = regs[rs]|imm
            elif op == 35:
                regs[rt] = memory[(regs[rs]+simm)&0xFFFFFFFF]
            elif op == 43:
                memory[(regs[rs]+simm)&0xFFFFFFFF] = regs[rt]
            elif op == 6:
                if signed(regs[rs]) <= 0:
                    delayed = pc+4+simm*4
            elif op in (2,3):
                delayed = ((pc+4)&0xF0000000)|((word&0x3FFFFFF)<<2)
                if op == 3:
                    regs[31] = pc+8
            elif op == 0 and word&63 == 3:
                regs[rd] = (signed(regs[rt]) >> ((word>>6)&31))&0xFFFFFFFF
            else:
                self.fail(f'Unexpected MIPS instruction {word:08x}')
            pc = old_delay if old_delay is not None else pc+4
        self.assertEqual(pc, entry+8)
        self.assertEqual(regs[16:24], before[16:24])
        self.assertEqual(regs[28], before[28])
        self.assertEqual(regs[30:], before[30:])
        self.assertEqual(regs[29], before[29]-96)
        self.assertEqual(regs[4], 0x09400000)
        self.assertEqual(memory[colour], 0x12345678)
        self.assertEqual(memory[font.scratch], 0xABCDEF01)
        return drawn, memory[state]

    def test_top_left_draw_restores_font_and_registers(self):
        drawn, remaining = self.execute(180)
        self.assertEqual(drawn, [(53, 28, 0x09900300, 0xFFFFFFFF, 0xFFFFFFFF)])
        self.assertEqual(remaining, 179)

    def test_expired_notification_skips_drawing(self):
        self.assertEqual(self.execute(0), ([], 0))

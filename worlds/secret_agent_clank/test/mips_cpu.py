"""Small instruction interpreter for native watchdog regression tests."""

class CPU:
    STOP = 0x1FFF00

    def __init__(self, memory):
        self.memory = memory
        self.r = [0] * 32
        self.r[31], self.r[29] = self.STOP, 0x1FF0000
        self.calls = []

    def run(self, pc, stop=None, stubs=(), max_steps=1000):
        stop = self.STOP if stop is None else stop
        delayed = None
        for _ in range(max_steps):
            if pc == stop: return
            if pc in stubs:
                self.calls.append(pc)
                if isinstance(stubs, dict):
                    stubs[pc](self)
                pc = self.r[31]
                continue
            instruction = self.memory.read_int32(pc)
            op, rs, rt = instruction >> 26, instruction >> 21 & 31, instruction >> 16 & 31
            rd, shift, fn = instruction >> 11 & 31, instruction >> 6 & 31, instruction & 63
            imm = instruction & 65535
            signed = imm - 65536 if imm & 32768 else imm
            destination, delayed = delayed, None
            addr = (self.r[rs] + signed) & 0xFFFFFFFF
            if instruction == 0: pass
            elif op == 0:
                if fn == 0: self.r[rd] = self.r[rt] << shift
                elif fn == 2: self.r[rd] = self.r[rt] >> shift
                elif fn in (0x21, 0x2D): self.r[rd] = self.r[rs] + self.r[rt]
                elif fn == 0x25: self.r[rd] = self.r[rs] | self.r[rt]
                elif fn == 0x2B: self.r[rd] = int(self.r[rs] < self.r[rt])
                elif fn == 8: delayed = self.r[rs]
                else: raise AssertionError(hex(instruction))
            elif op == 2:
                delayed = (instruction & 0x3FFFFFF) << 2
            elif op == 3:
                self.r[31] = pc + 8
                delayed = (instruction & 0x3FFFFFF) << 2
            elif op == 4:
                if self.r[rs] == self.r[rt]: delayed = pc + 4 + signed * 4
            elif op == 5:
                if self.r[rs] != self.r[rt]: delayed = pc + 4 + signed * 4
            elif op == 9: self.r[rt] = self.r[rs] + signed
            elif op == 11: self.r[rt] = int(self.r[rs] < (signed & 0xFFFFFFFF))
            elif op == 12: self.r[rt] = self.r[rs] & imm
            elif op == 13: self.r[rt] = self.r[rs] | imm
            elif op == 14: self.r[rt] = self.r[rs] ^ imm
            elif op == 15: self.r[rt] = imm << 16
            elif op == 35: self.r[rt] = self.memory.read_int32(addr)
            elif op == 36: self.r[rt] = self.memory.read_int8(addr)
            elif op == 40: self.memory.write_int8(addr, self.r[rt] & 255)
            elif op == 43: self.memory.write_int32(addr, self.r[rt])
            elif op == 55: self.r[rt] = int.from_bytes(self.memory.read_bytes(addr, 8), "little")
            elif op == 63: self.memory.write_bytes(addr, self.r[rt].to_bytes(8, "little"))
            else: raise AssertionError(hex(instruction))
            self.r = [x & 0xFFFFFFFF for x in self.r]
            self.r[0] = 0
            pc = destination if destination is not None else pc + 4
        raise AssertionError("Native code did not return")


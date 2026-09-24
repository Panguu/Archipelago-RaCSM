"""Small checked encoder for the integer instructions used by the patches/*.S hooks.

Not a general assembler. Rejects unsupported syntax rather than producing guessed code.
Output is independently checked with Capstone before installation.
"""
import re
import struct


def assemble(source):
    variables, labels, instructions = {}, {}, []
    lines = [line.split('#')[0].strip() for line in source.splitlines()]

    def value(expr):
        parts = expr.strip().split('+')
        return sum(variables[p] if p in variables else int(p,0) for p in parts)

    def expand(block):
        i = 0
        while i < len(block):
            line = block[i]; i += 1
            if not line or line.startswith(('.text','.globl')):
                continue
            if line.startswith('.set '):
                name, expr = line[5:].split(',')
                variables[name.strip()] = value(expr)
            elif line.startswith('.rept '):
                end = block.index('.endr', i)
                for _ in range(value(line[6:])):
                    expand(block[i:end])
                i = end+1
            elif line.endswith(':'):
                labels[line[:-1]] = len(instructions)*4
            else:
                mnemonic, _, operands = line.partition(' ')
                args = [x.strip() for x in operands.split(',')] if operands else []
                if mnemonic not in ('b','bne','bge','beq','bgt'):
                    args = [re.sub(r'\boffset\b',str(variables.get('offset',0)),x) for x in args]
                instructions.append((mnemonic,args))
    expand(lines)

    def reg(arg):
        n = value(arg)
        if not 0 <= n <= 31: raise ValueError('Invalid register')
        return n

    def d(op, rt, ra, imm):
        if not -32768 <= imm <= 65535: raise ValueError('Immediate out of range')
        return op<<26 | rt<<21 | ra<<16 | (imm&0xffff)

    result = []
    for pc,(op,args) in enumerate(instructions):
        if op in ('stdu','std','ld','lwz','stw','lbz','stb','lfs','stfs'):
            rt = reg(args[0]); m = re.fullmatch(r'(.+)\((\d+)\)',args[1])
            if not m: raise ValueError('Invalid memory operand')
            offset, ra = value(m[1]),reg(m[2])
            if op in ('stdu','std','ld') and offset%4: raise ValueError('Unaligned DS displacement')
            word = d({'stdu':62,'std':62,'ld':58,'lwz':32,'stw':36,'lbz':34,'stb':38,'lfs':48,'stfs':52}[op],rt,ra,offset)
            if op=='stdu': word |= 1
        elif op in ('li','lis'):
            word = d(14 if op=='li' else 15, reg(args[0]),0,value(args[1]))
        elif op in ('addi','mulli'):
            word = d(14 if op=='addi' else 7,reg(args[0]),reg(args[1]),value(args[2]))
        elif op in ('ori','andi.'):
            word = d(24 if op=='ori' else 28,reg(args[1]),reg(args[0]),value(args[2]))
        elif op in ('cmpwi','cmplwi'):
            word = d(11 if op=='cmpwi' else 10,0,reg(args[0]),value(args[1]))
        elif op in ('add','subf'):
            word = 31<<26 | reg(args[0])<<21 | reg(args[1])<<16 | reg(args[2])<<11 | (266 if op=='add' else 40)<<1
        elif op in ('lvx', 'stvx'):
            word = 31<<26 | reg(args[0])<<21 | reg(args[1])<<16 | reg(args[2])<<11 | (103 if op == 'lvx' else 231)<<1
        elif op == 'cmpw':
            word = 0x7c000000 | reg(args[0])<<16 | reg(args[1])<<11
        elif op in ('b','bne','bge','beq','bgt'):
            delta = labels[args[0]]-pc*4
            if delta%4 or not -32768 <= delta < 32768: raise ValueError('Branch out of range')
            word = (0x48000000 | delta&0x3fffffc) if op=='b' else (
                {'bne':0x40820000,'bge':0x40800000,'beq':0x41820000,'bgt':0x41810000}[op] | delta&0xfffc)
        elif op in ('mflr','mtlr','mtctr'):
            word = {'mflr':0x7c0802a6,'mtlr':0x7c0803a6,'mtctr':0x7c0903a6}[op] | reg(args[0])<<21
        elif op == '.word': word = value(args[0])
        elif op == 'bctrl': word = 0x4e800421
        elif op == 'blr': word = 0x4e800020
        elif op=='mfcr': word = 0x7c000026 | reg(args[0])<<21
        elif op=='mtcr': word = 0x7c0ff120 | reg(args[0])<<21
        elif op=='sync': word = 0x7c0004ac
        else: raise ValueError(f'Unsupported instruction {op}')
        result.append(word)
    return b''.join(struct.pack('>I',word) for word in result)

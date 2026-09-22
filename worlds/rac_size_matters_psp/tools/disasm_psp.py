import sys,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.research/deps'))
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
r=Path(__file__).resolve().parents[1]/'.research/ram.bin'
b=r.read_bytes(); start=0x08000000
cs=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
cs.skipdata=True
if sys.argv[1]=='dis':
    address=int(sys.argv[2],0); size=int(sys.argv[3],0) if len(sys.argv)>3 else 0x100
    for i in cs.disasm(b[address-start:address-start+size],address): print(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic:8s} {i.op_str}')
else:
    target=int(sys.argv[2],0); radius=int(sys.argv[3],0) if len(sys.argv)>3 else 0
    words=struct.unpack('<%dI'%(len(b)//4),b)
    regs={0:0}
    for n,v in enumerate(words):
        op=v>>26;rs=(v>>21)&31;rt=(v>>16)&31;rd=(v>>11)&31;imm=v&65535; signed=imm-65536 if imm&32768 else imm
        value=None
        if op==15: value=imm<<16
        elif op in (8,9) and rs in regs: value=(regs[rs]+signed)&0xffffffff
        elif op==13 and rs in regs: value=regs[rs]|imm
        elif op==0 and (v&63) in (33,37) and rs in regs and rt in regs:
            value=(regs[rs]+regs[rt])&0xffffffff;rt=rd
        if op in (32,33,35,36,37,40,41,43,49,57) and rs in regs:
            addr=(regs[rs]+signed)&0xffffffff
            if abs(addr-target)<=radius:
                ins=next(cs.disasm(struct.pack('<I',v),start+n*4));print(f'{ins.address:08x} -> {addr:08x} {ins.mnemonic} {ins.op_str}')
        if value is not None: regs[rt]=value
        elif op in (32,33,35,36,37,8,9,13,15):regs.pop(rt,None)
        elif op==0 and (v&63) not in (8,9):regs.pop(rd,None)
        if v==0x03e00008:regs={0:0}
        regs[0]=0

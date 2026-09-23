"""Build standalone skin PNACHs. Python/Archipelago are build-time dependencies only.

The EE installer runs at the relocated-module loader boundary. It locates the
skin routines, resolves their native calls, then installs the same loader used
by multiplayer_skins.prepare. No vendor, item or network hooks are installed.
"""

import json
import struct
from pathlib import Path
from types import SimpleNamespace

from ..core.patches import asm as m, multiplayer_skins as mp
from ..core.patches.asm import packed
from ..core.patches.loader_gate import LoaderGate

ROOT = Path(__file__).resolve().parents[1]
REGIONS = {
    "us": ("SCUS-97615", "8661F7BA", "pokitaru", 0x1104400, 0x1F4B45A),
    "eu": ("SCES-55019", "FCB981D5", "eu_pokitaru", 0x1104000, 0x1F4B45A),
    "jp": ("SCPS-15120", "9ADCF7AF", "jp_pokitaru", 0x1106000, 0x1F4B29A),
}


class Memory:
    def __init__(self, fixture):
        self.data = bytearray(0x2000000)
        self.game_id = fixture.get("game_id", "SCUS-97615")
        for address, data in fixture["segments"]:
            self.data[address:address + len(data) // 2] = bytes.fromhex(data)

    def get_game_id(self):
        return self.game_id

    def read_bytes(self, address, size):
        return bytes(self.data[address:address + size])

    def read_int32(self, address):
        return struct.unpack_from("<I", self.data, address)[0]

    def write_bytes(self, address, data):
        self.data[address:address + len(data)] = data

    def write_int32(self, address, value):
        self.write_bytes(address, packed(value))


def fixture(region):
    rows = json.loads((ROOT / f"test/fixtures/multiplayer_skins_{region}.json").read_text())
    return rows[REGIONS[region][2]]


def make_plan(memory, f):
    skin = SimpleNamespace(begin=f["begin"], finish=f["finish"],
                           menu_anchor=f["gate"], edits=[SimpleNamespace(address=f["gate"] + 4)])
    return mp.prepare(memory, code_start=f["base"],
                      code=memory.read_bytes(f["base"], 0x280000), skin=skin)


def sources(jp):
    # Anchor register, instruction offset(s); one = JAL, two = LUI/ADDIU.
    return {
        "size": (m.S2, (0xAC,)), "load": (m.S2, (0xE4,)),
        "asset": (m.S3, (0xB4,)), "pak": (m.S2, (0xA4, 0xB0)),
        "pending": (m.S3, (4, 16)), "changed": (m.S3, (0x98, 0xA4)),
        "apply": (m.S3, (0x9C, 0xA8)),
        "owned": (m.S1, (-0x914 if jp else -0x91C,)),
        "gettext": (m.S1, (-0x8A0 if jp else -0x8A8,)),
        "add": (m.S1, (0x24 if jp else 0x28,)),
    }


def decode(memory, anchor, offsets):
    if len(offsets) == 1:
        return (memory.read_int32(anchor + offsets[0]) & 0x3FFFFFF) << 2
    hi, lo = (memory.read_int32(anchor + o) for o in offsets)
    return ((hi & 65535) << 16) + struct.unpack("<h", packed(lo)[:2])[0]


def template(region):
    """Derive relocations by perturbing each input to the existing plan builder.

    Every changed output word must match a supported address encoding. This
    fails the build if the loader starts using an unhandled address encoding.
    """
    f = fixture(region)
    memory = Memory(f)
    plan = make_plan(memory, f)
    anchors = {m.S1: f["gate"], m.S2: f["begin"], m.S3: f["finish"]}
    variables, fixups = list(sources(region == "jp")), {}
    for var, (reg, offsets) in sources(region == "jp").items():
        changed = Memory(f)
        anchor = anchors[reg]
        old = decode(memory, anchor, offsets)
        new = ((old + 0x20000) & 0xFFFF0000) | ((old & 65535) ^ 0x8120)
        if len(offsets) == 1:
            changed.write_int32(anchor + offsets[0], m.jump(new))
            if var == "owned":
                for off in ((-0x720, 0xF8) if region == "jp" else (-0x728, 0x108)):
                    changed.write_int32(f["gate"] + off, m.jump(new))
        else:
            hi, lo = (anchor + o for o in offsets)
            changed.write_int32(hi, (changed.read_int32(hi) & 0xFFFF0000) | ((new + 0x8000) >> 16))
            changed.write_int32(lo, (changed.read_int32(lo) & 0xFFFF0000) | (new & 65535))
        other = make_plan(changed, f)
        assert len(plan.edits) == len(other.edits)
        for edit, altered in zip(plan.edits, other.edits):
            assert edit.address == altered.address
            if edit.address == plan.buffer + 0x75700:
                continue  # Stock finish is copied directly from the live module.
            assert len(edit.replacement) == len(altered.replacement)
            for off in range(0, len(edit.replacement) - 3, 4):
                a = struct.unpack_from("<I", edit.replacement, off)[0]
                b = struct.unpack_from("<I", altered.replacement, off)[0]
                if a == b:
                    continue
                prefix = a & 0xFFFF0000
                encodings = {
                    "value": lambda v: v,
                    "jal": m.jump, "j": m.j,
                    "hi": lambda v: prefix | ((v + 0x8000) >> 16),
                    "lui": lambda v: prefix | (v >> 16),
                    "lo": lambda v: prefix | (v & 65535),
                }
                kind = next((k for k, fn in encodings.items() if fn(old) == a and fn(new) == b), None)
                if kind is None:
                    raise ValueError(f"Unsupported relocation: {var} {edit.address + off:#x}")
                key = edit.address + off
                if key in fixups:
                    raise ValueError("Overlapping relocations")
                fixups[key] = (variables.index(var), kind, prefix)
    return memory, f, plan, variables, fixups


class Code(mp._Code):
    def __init__(self):
        super().__init__()
        self.counter = 0

    def name(self, prefix):
        self.counter += 1
        return f"{prefix}_{self.counter}"

    def imm(self, reg, value):
        self.emit(*m.li32(reg, value))

    def guard(self, reg, value):
        self.imm(m.T9, value)
        self.branch(m.bne(reg, m.T9, 0), "return")

    def pointer(self, dest, base, hi, lo):
        self.emit(m.lw(dest, hi, base), m.sll(dest, dest, 16),
                  m.lw(m.T8, lo, base), m.andi(m.T8, m.T8, 65535),
                  m.xori(m.T8, m.T8, 0x8000), m.addiu(m.T8, m.T8, -32768),
                  m.addu(dest, dest, m.T8))

    def call_target(self, dest, base, offset):
        self.emit(m.lw(dest, offset, base), m.sll(dest, dest, 6), m.srl(dest, dest, 4))

    def copy(self, source, dest, size):
        assert size % 4 == 0
        if source is not None:
            self.imm(m.T0, source)
        self.imm(m.T1, dest)
        self.imm(m.T2, size)
        loop = self.name("copy")
        self.label(loop)
        self.emit(m.lw(m.T3, 0, m.T0), m.sw(m.T3, 0, m.T1),
                  m.addiu(m.T0, m.T0, 4), m.addiu(m.T1, m.T1, 4),
                  m.addiu(m.T2, m.T2, -4))
        self.branch(m.bne(m.T2, m.ZERO, 0), loop)


def build(region):
    memory, f, plan, variables, fixups = template(region)
    game_id, crc, _, buffer, skin_byte = REGIONS[region]
    jp = region == "jp"
    gate = LoaderGate(memory, game_id=game_id)
    entry, data_start = buffer + 0x76000, buffer + 0x7C000
    c, data = Code(), bytearray()
    regs = list(range(1, 26)) + [28, 30, 31]
    c.emit(m.addiu(m.SP, m.SP, -0x200))
    for i, reg in enumerate(regs):
        c.emit(m.sd(reg, i * 8, m.SP))
    c.imm(m.T0, mp.mcp_address(game_id) + 0x2DC)
    c.emit(m.lw(m.T1, 0, m.T0))
    c.guard(m.T1, buffer)
    c.imm(m.T0, gate.STATE)
    c.emit(m.lw(m.T1, 0, m.T0))
    c.guard(m.T1, 4)
    c.imm(m.T0, gate.LOAD_THREAD)
    c.emit(m.lw(m.T1, 0, m.T0))
    c.guard(m.T1, 0)
    c.imm(m.T0, gate.HANDLE)
    c.emit(m.lw(m.T1, 0, m.T0), m.sltiu(m.T2, m.T1, 8))
    c.guard(m.T2, 1)
    c.emit(m.sll(m.T2, m.T1, 10), m.sll(m.T3, m.T1, 4),
           m.addu(m.T2, m.T2, m.T3), m.sll(m.T3, m.T1, 3), m.addu(m.T2, m.T2, m.T3))
    c.imm(m.T0, gate.MODULES)
    c.emit(m.addu(m.T0, m.T0, m.T2), m.lw(m.S0, 4, m.T0),
           m.lw(m.T1, 8, m.T0), m.andi(m.T1, m.T1, 1))
    c.guard(m.T1, 1)
    c.imm(m.T0, 0x100000)
    c.emit(m.sltu(m.T1, m.S0, m.T0))
    c.guard(m.T1, 0)
    c.imm(m.T0, 0x1B80000)
    c.emit(m.sltu(m.T1, m.S0, m.T0))
    c.guard(m.T1, 1)
    c.emit(m.move(m.S5, m.S0), m.move(m.S1, m.ZERO), m.move(m.S7, m.ZERO))
    c.imm(m.T0, 0x27FFC0)
    c.emit(m.addu(m.S6, m.S0, m.T0))
    c.label("scan")
    patterns = [
        (m.S1, [0x8E050000, 0x0220302D, 0xAFB30000, 0x0240202D, 0x0000382D]
         if jp else [0x8E030000, 0x1074000A, 0x0240202D, 0x8E050008]),
        (m.S7, [0x806402E0, 0x10A40007]),
    ]
    for dest, pattern in patterns:
        skip = c.name("next_signature")
        for i, word in enumerate(pattern):
            c.emit(m.lw(m.T0, i * 4, m.S5))
            c.imm(m.T1, word)
            c.branch(m.bne(m.T0, m.T1, 0), skip)
        c.branch(m.bne(dest, m.ZERO, 0), "return")
        c.emit(m.move(dest, m.S5))
        c.label(skip)
    c.emit(m.addiu(m.S5, m.S5, 4), m.sltu(m.T0, m.S5, m.S6))
    c.branch(m.bne(m.T0, m.ZERO, 0), "scan")
    c.branch(m.beq(m.S1, m.ZERO, 0), "return")
    c.branch(m.beq(m.S7, m.ZERO, 0), "return")
    c.call_target(m.S2, m.S7, 16)
    c.call_target(m.S3, m.S7, 24)
    for reg, offset, value in ((m.S2, 0, 0x27BDFFB0), (m.S3, 0, 0x27BDFFB0),
                               (m.S7, 12, 0x00A0202D), (m.S7, 20, 0x24050001)):
        c.emit(m.lw(m.T0, offset, reg))
        c.guard(m.T0, value)
    c.pointer(m.S4, m.S1, -0x1C, -0x18)
    for i, model in enumerate((0, 1, 2, 6, 3, 5, 4)):
        c.emit(m.lw(m.T0, i * 16, m.S4))
        c.guard(m.T0, model)
    # Resolve all inputs before changing any instruction.
    for i, (reg, offsets) in enumerate(sources(jp).values()):
        if len(offsets) == 1:
            c.call_target(m.T0, reg, offsets[0])
        else:
            c.pointer(m.T0, reg, *offsets)
        c.emit(m.sw(m.T0, 0x100 + i * 4, m.SP))

    def destination(address):
        if f["begin"] <= address < f["begin"] + 0x180:
            return m.S2, address - f["begin"]
        if f["finish"] <= address < f["finish"] + 8:
            return m.S3, address - f["finish"]
        if f["gate"] - 0x1000 <= address < f["gate"] + 0x1000:
            return m.S1, address - f["gate"]
        return None

    code_edits = [e for e in plan.edits if destination(e.address) is not None]
    # Validate every instruction being replaced; pointer immediates relocate.
    for edit in code_edits:
        reg, off = destination(edit.address)
        for i in range(0, len(edit.original), 4):
            word = struct.unpack_from("<I", edit.original, i)[0]
            c.emit(m.lw(m.T0, off + i, reg))
            if word >> 26 == 3:
                c.emit(m.srl(m.T0, m.T0, 26))
                word >>= 26
            elif word >> 26 in (15, 9) and edit.address not in range(f["begin"], f["begin"] + 0x180):
                c.emit(m.srl(m.T0, m.T0, 16))
                word >>= 16
            c.guard(m.T0, word)

    # Initialize storage only once per relocated module, never every frame.
    c.imm(m.T0, plan.rows)
    c.imm(m.T1, 0x2000)
    c.label("zero_rows")
    c.emit(m.sw(m.ZERO, 0, m.T0), m.addiu(m.T0, m.T0, 4), m.addiu(m.T1, m.T1, -4))
    c.branch(m.bne(m.T1, m.ZERO, 0), "zero_rows")
    for edit in plan.edits:
        if edit in code_edits or edit.address in (plan.rows, mp.mcp_address(game_id) + 0x2D4):
            continue
        if edit.address == buffer + 0x75700:
            c.emit(m.move(m.T0, m.S3))
            c.copy(None, edit.address, len(edit.replacement))
            continue
        payload = edit.replacement
        start = data_start + len(data)
        data += payload + bytes((-len(payload)) % 4)
        c.copy(start, edit.address, (len(payload) + 3) & ~3)
    c.emit(m.move(m.T0, m.S4))
    c.copy(None, plan.table, 7 * 16)
    sp_table = {"us": mp.SP_TABLE, "eu": 0x1EDCA10, "jp": 0x1EDE938}[region]
    c.copy(sp_table, plan.descriptors, 7 * 24)
    for dest, (var, kind, prefix) in fixups.items():
        c.emit(m.lw(m.T0, 0x100 + var * 4, m.SP))
        if kind in ("j", "jal"):
            c.emit(m.srl(m.T0, m.T0, 2))
            c.imm(m.T1, 0x08000000 if kind == "j" else 0x0C000000)
            c.emit(m.or_(m.T0, m.T0, m.T1))
        elif kind in ("hi", "lui", "lo"):
            if kind == "hi":
                c.imm(m.T1, 0x8000)
                c.emit(m.addu(m.T0, m.T0, m.T1))
            c.emit(m.andi(m.T0, m.T0, 65535) if kind == "lo" else m.srl(m.T0, m.T0, 16))
            c.imm(m.T1, prefix)
            c.emit(m.or_(m.T0, m.T0, m.T1))
        c.imm(m.T1, dest)
        c.emit(m.sw(m.T0, 0, m.T1))
    # Publish pointers and code only after initializing the payload.
    c.imm(m.T0, mp.mcp_address(game_id) + 0x2D4)
    c.imm(m.T1, plan.descriptors)
    c.emit(m.sw(m.T1, 0, m.T0))
    for edit in code_edits:
        reg, off = destination(edit.address)
        for i in range(0, len(edit.replacement), 4):
            c.imm(m.T0, struct.unpack_from("<I", edit.replacement, i)[0])
            c.emit(m.sw(m.T0, off + i, reg))
    if not jp:
        c.emit(m.sw(m.ZERO, 4, m.S1))  # Include Trash Ratchet's native row.
    c.imm(m.T0, skin_byte)
    c.emit(m.addiu(m.T1, m.ZERO, 0x7F), m.sb(m.T1, 0, m.T0))
    # FlushCache(0), FlushCache(2): publish generated data and executable code.
    for mode in (0, 2):
        c.emit(m.addiu(m.A0, m.ZERO, mode), m.addiu(m.V1, m.ZERO, 0x64), 0x0000000C)
    c.label("return")
    for i, reg in enumerate(regs):
        c.emit(m.ld(reg, i * 8, m.SP))
    c.emit(m.addiu(m.SP, m.SP, 0x200), gate.ORIGINAL,
           m.j(gate.SITE + 8), gate.SIGNATURE[6])
    payload = c.pack()
    assert entry + len(payload) <= data_start
    assert data_start + len(data) < buffer + 0x7F000  # Secondary textures start here.
    return SimpleNamespace(entry=entry, code=payload, data_address=data_start, data=bytes(data),
                           gate=gate, buffer=buffer, skin_byte=skin_byte, plan=plan,
                           fixture=f, crc=crc, game_id=game_id)


def conditional(commands, guards):
    """All commands use RAW extended encoding; nested skips count actual lines."""
    assert len(commands) + len(guards) <= 255
    lines = []
    for i, (address, value, unequal) in enumerate(guards):
        count = len(commands) + len(guards) - i - 1
        lines.append(f"patch=1,EE,E0{count:02X}{value:04X},extended,{address | (0x10000000 if unequal else 0):08X}")
    return lines + [f"patch=1,EE,{address:08X},extended,{value:08X}" for address, value in commands]


def pnach(result):
    lines = [f"gametitle=Ratchet & Clank: Size Matters ({result.game_id})", "",
             "[All single-player and multiplayer skins]",
             "description=Unlock 7 single-player and 13 multiplayer skins. Standalone; cold boot required. Do not combine with the Archipelago client.",
             "// Generated by tools/build_skin_pnach.py; no client or PINE required."]
    pointer = mp.mcp_address(result.game_id) + 0x2DC
    guards = [(pointer, result.buffer & 65535, False), (pointer + 2, result.buffer >> 16, False)]
    for address, data in ((result.entry, result.code), (result.data_address, result.data)):
        words = [(0x20000000 | (address + i), struct.unpack_from("<I", data, i)[0]) for i in range(0, len(data), 4)]
        for start in range(0, len(words), 200):
            lines += conditional(words[start:start + 200], guards)
    site = result.gate.SITE
    # Publish the hook last, only over the verified resident instructions.
    signature_guards = []
    for address, value in ((site, result.gate.ORIGINAL), (site + 4, result.gate.SIGNATURE[6])):
        signature_guards += [(address, value & 65535, False), (address + 2, value >> 16, False)]
    lines += conditional([(0x20000000 | site, m.j(result.entry)), (0x20000000 | (site + 4), 0)], guards + signature_guards)
    # Remove our hook if the game releases/moves the hero buffer.
    hook_guards = [(site, m.j(result.entry) & 65535, False), (site + 2, m.j(result.entry) >> 16, False)]
    for address, value, _ in guards:
        lines += conditional([(0x20000000 | site, result.gate.ORIGINAL),
                              (0x20000000 | (site + 4), result.gate.SIGNATURE[6])],
                             [(address, value, True)] + hook_guards)
    return "\n".join(lines) + "\n"


def main():
    output = ROOT / "standalone_skins"
    output.mkdir(exist_ok=True)
    for region in REGIONS:
        result = build(region)
        name = f"{result.game_id}_{result.crc or 'REPLACE_WITH_GAME_CRC'}.pnach"
        (output / name).write_text(pnach(result), encoding="utf-8")
        print(region, name, len(result.code), len(result.data))


if __name__ == "__main__":
    main()

"""Expose the story destinations in the US ship menu.

Reuse the obsolete visibility predicate for the loop tail and the obsolete
Omega redirect for labels. No allocation, save flags, or ISO changes. Two
Omega rows share native planet 6's display metadata; +0xd4 distinguishes the
first visit from the return visit when confirming travel.
"""
import struct

from . import mips as m
from .asm import Patch, branch, j, jump, packed
from .plan import Plan


def prepare(pine, *, code_start, code):
    if pine.get_game_id() != "SCUS-97615":
        raise RuntimeError("Ship menu patch requires SCUS-97615")
    anchor = packed(0x26310001, 0x2E22000C, 0x1440FFE4, 0x0000802D)
    hits = [i for i in range(0, len(code) - len(anchor) + 1, 4)
            if code[i:i + len(anchor)] == anchor]
    if len(hits) != 1:
        raise RuntimeError("Expected one native ship menu builder")
    end = code_start + hits[0] + 16
    loop = end - 120

    def read(address, size):
        offset = address - code_start
        if not 0 <= offset <= len(code) - size:
            raise RuntimeError("Ship menu outside loaded module")
        return code[offset:offset + size]

    def require(address, expected):
        if read(address, len(expected)) != expected:
            raise RuntimeError(f"Ship menu signature changed at {address:#x}")

    def call(address):
        word, = struct.unpack("<I", read(address, 4))
        if word >> 26 != 3:
            raise RuntimeError("Ship menu call signature changed")
        return (word & 0x3FFFFFF) << 2

    unlock = call(loop + 4)
    tail = call(loop + 20)
    group = call(loop + 44)
    name = call(loop + 56)
    add = call(loop + 96)
    original_loop = packed(
        0x0000802D, jump(unlock), 0x0220202D, 0x10400004, 0,
        jump(tail), 0x0220202D, 0x0282800B, 0x12000011,
        0x24060001, 0x0260202D, jump(group), 0x24050001,
        0x0220202D, jump(name), 0x0000282D, 0x0040282D,
        0xAFB20000, 0x0260202D, 0x0220302D, 0x0000382D,
        0x0000402D, 0x0000482D, 0x240A0001, jump(add),
        0x0000582D, 0x26310001, 0x2E22000C, 0x1440FFE4, 0x0000802D,
    )
    require(loop, original_loop)
    require(tail, packed(0x2483FFFF, 0x2C62000A, 0x10400009, 0x0000282D))
    require(tail + 44, packed(0x24050001, 0x03E00008, 0x00A0102D))
    # Check the switch table as well as its dispatch instructions.
    words = struct.unpack("<7I", read(tail + 16, 28))
    if (words[0] >> 16 != 0x3C02 or words[1] != 0x00031880
            or words[2] >> 16 != 0x2442
            or words[3:] != (0x00621821, 0x8C640000, 0x00800008, 0)):
        raise RuntimeError("Ship visibility switch changed")
    low = words[2] & 0xFFFF
    table = ((words[0] & 0xFFFF) << 16) + (low - 0x10000 if low & 0x8000 else low)
    require(table, packed(*(tail + (48 if p in (5, 9) else 44) for p in range(1, 11))))

    route = end - 0x8E8
    setter = call(route + 36)
    visited = call(route + 20)
    require(route - 4, packed(0x1083FFEB))
    require(route, packed(
        0x24020006, 0x1482000F, 0x24020017, 0x1062FFE7, 0,
        jump(visited), 0x24040017, 0x10400005, 0,
        jump(setter), 0x24040017, 0x10000007, 0,
        jump(setter), 0x8E0400D0, 0x10000003, 0,
        jump(setter), 0,
    ))
    label = route + 52
    # The first Omega row carries marker 1; the second carries marker 0.
    # Dreamtime (5) uses Outpost's unlock (6), irrespective of its auto-unlock.
    body = [
        m.xori(m.V0, m.S1, 5), m.sltiu(m.V0, m.V0, 1),
        jump(unlock), m.addu(m.A0, m.S1, m.V0),
        m.beq(m.V0, m.ZERO, (tail + 8 - (loop + 20)) // 4), m.dmove(m.A0, m.S3),
        m.addiu(m.A1, m.ZERO, 1), jump(group), m.addiu(m.A2, m.ZERO, 1),
        m.dmove(m.A0, m.S1), jump(name), m.dmove(m.A1, m.ZERO),
        m.dmove(m.A1, m.V0), m.addiu(m.V0, m.ZERO, 6),
        m.bne(m.S1, m.V0, 5), m.sw(m.S2, 0, m.SP),
        *m.li32(m.A1, label),
        m.sll(m.V0, m.S4, 3), m.addu(m.A1, m.A1, m.V0),
        m.dmove(m.A0, m.S3), m.dmove(m.A2, m.S1), m.dmove(m.A3, m.S4),
        m.dmove(m.T0, m.ZERO), m.dmove(m.T1, m.ZERO), m.addiu(m.T2, m.ZERO, 1),
        j(tail), m.dmove(m.T3, m.ZERO),
    ]
    continuation = [
        jump(add), m.NOP, m.addiu(m.V0, m.ZERO, 6),
        m.bne(m.S1, m.V0, 3), m.NOP,
        m.bne(m.S4, m.ZERO, (loop - (tail + 24)) // 4), m.addiu(m.S4, m.ZERO, 0),
        m.addiu(m.S1, m.S1, 1), m.sltiu(m.V0, m.S1, 11),
        m.bne(m.V0, m.ZERO, (loop - (tail + 40)) // 4), m.addiu(m.S4, m.ZERO, 1),
        j(end), m.NOP,
    ]
    routing = packed(
        m.addiu(m.V0, m.ZERO, 6), m.bne(m.A0, m.V0, 5), m.NOP,
        m.lw(m.V0, 0xD4, m.S0), m.bne(m.V0, m.ZERO, 2), m.NOP,
        m.addiu(m.A0, m.ZERO, 23),
        m.beq(m.A0, m.V1, ((route - 0x54) - (route + 32)) // 4), m.NOP,
        jump(setter), m.NOP, branch(route + 44, route + 76), m.NOP,
    ) + b"MOO2\0\0\0\0MOO1\0"
    edits = [
        Patch(loop, original_loop, packed(*body).ljust(120, b"\0")),
        Patch(tail, read(tail, 56), packed(*continuation).ljust(56, b"\0")),
        Patch(route - 4, packed(0x1083FFEB), packed(m.NOP)),
        Patch(route, read(route, 76), routing.ljust(76, b"\0")),
    ]
    return Plan(pine, edits)

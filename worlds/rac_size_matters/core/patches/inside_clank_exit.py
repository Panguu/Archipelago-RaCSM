"""Suppress the completion cinematic only for Inside Clank ship-menu exits.

The departure evaluator treats Quodrona ownership as an escape objective.
A marker scoped to this loaded module distinguishes voluntary menu travel
from the ordinary scripted completion route. No save bits are changed.
"""
import struct

from . import mips as m
from .asm import Patch, j, jump, packed
from .plan import Plan


def prepare(pine, *, code_start, code, arena, gate):
    if gate.pine is not pine or gate.held_module() != (9, code_start):
        raise RuntimeError("Inside Clank must be held before level startup")

    def unique(signature):
        hits = [i for i in range(0, len(code) - len(signature) + 1, 4)
                if code[i:i + len(signature)] == signature]
        if len(hits) != 1:
            raise RuntimeError("Inside Clank departure signature changed")
        return code_start + hits[0]

    def read(address, size):
        offset = address - code_start
        if not 0 <= offset <= len(code) - size:
            raise RuntimeError("Inside Clank departure outside loaded module")
        return code[offset:offset + size]

    transition = unique(packed(0x27BDFFF0, 0xFFB00000, 0xFFBF0008,
                               0x10A00006, 0x0080802D))
    menu_call = unique(packed(0x24050001, jump(transition))) + 4
    if int.from_bytes(read(menu_call + 4, 4), 'little') & 0xFFFF0000 != 0x8C440000:
        raise RuntimeError("Inside Clank ship destination load changed")
    completion_call = unique(packed(0x2402000A, 0x0043102B, 0x10400002)) - 16
    original, delay, move = struct.unpack('<3I', read(completion_call, 12))
    if original >> 26 != 3 or delay != 0x0200882D or move != 0x0040202D:
        raise RuntimeError("Inside Clank completion call changed")
    evaluator = (original & 0x3FFFFFF) << 2
    if read(evaluator, 12) != packed(0x27BDFFA0, 0xFFB30028, 0x0080982D):
        raise RuntimeError("Inside Clank mission evaluator changed")

    entry, completion, flag = arena + 0x300, arena + 0x320, arena + 0x360
    menu_code = packed(*m.li32(m.T0, flag), m.addiu(m.T1, m.ZERO, 1),
                       m.sw(m.T1, 0, m.T0), j(transition), m.NOP)
    check_code = packed(
        *m.li32(m.T0, flag), m.lw(m.T0, 0, m.T0),
        m.beq(m.T0, m.ZERO, 3), m.NOP,
        m.jr(m.RA), m.daddu(m.V0, m.ZERO, m.ZERO),
        j(evaluator), m.NOP)
    payload = menu_code.ljust(completion - entry, b'\0') + check_code
    payload = payload.ljust(flag - entry + 4, b'\0')
    plan = Plan(pine, [Patch(entry, pine.read_bytes(entry, len(payload)), payload),
                       Patch(menu_call, packed(jump(transition)), packed(jump(entry))),
                       Patch(completion_call, packed(original), packed(jump(completion)))])
    plan.mutable_data = ((flag, 4),)
    plan.entry, plan.completion, plan.flag = entry, completion, flag
    plan.transition, plan.evaluator = transition, evaluator
    return plan

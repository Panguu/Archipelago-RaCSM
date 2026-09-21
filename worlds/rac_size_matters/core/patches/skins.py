"""Expose Trash Ratchet and apply queued skins using the native menu routines.

Save/menu ids differ from HEROSKIN model ids. The callback runs on the game
thread, before the HUD renderer, and consumes requests only in gameplay.
Storage is in the vendor's validated, reserved upper half of its row array.
"""
import struct

from . import mips as m
from .asm import Patch, jump, packed
from .loader_gate import LoaderGate
from .plan import Plan

MODEL_IDS = (0, 5, 4, 6, 3, 1, 2) + tuple(range(7, 20))


def prepare(pine, *, code_start, code, arena, menu, model_count=7):
    if model_count not in (7, len(MODEL_IDS)):
        raise ValueError('Unsupported skin model count')
    if pine.get_game_id() != "SCUS-97615":
        raise RuntimeError("Skin patch requires US PS2 Size Matters")
    def read(address, size):
        offset = address - code_start
        if not 0 <= offset <= len(code) - size:
            raise RuntimeError("Skin code outside loaded module")
        return code[offset:offset + size]

    def unique(signature):
        hits = [i for i in range(0, len(code) - len(signature) + 1, 4)
                if code[i:i + len(signature)] == signature]
        if len(hits) != 1:
            raise RuntimeError("Expected one native skin menu signature")
        return code_start + hits[0]

    def call(address):
        word, = struct.unpack('<I', read(address, 4))
        if word >> 26 != 3:
            raise RuntimeError("Native skin call changed")
        return (word & 0x3FFFFFF) << 2

    gate = unique(packed(0x8E030000, 0x1074000A, 0x0240202D, 0x8E050008))
    close = unique(packed(0x806402E0, 0x10A40007))
    if read(close + 12, 4) != packed(0x00A0202D) or read(close + 20, 4) != packed(0x24050001):
        raise RuntimeError("Native skin application sequence changed")
    begin, finish = call(close + 16), call(close + 24)
    if (read(begin, 4) != packed(0x27BDFFB0)
            or read(begin + 12, 4) != packed(0x2407FFFF)
            or read(finish, 4) != packed(0x27BDFFB0)
            or read(finish + 12, 4) != packed(0x2402FFFF)):
        raise RuntimeError("Native skin loader changed")
    # Reuse the menu's save-pointer load and model-id store after a successful
    # load. This is distinct from the saved menu selection byte at SKIN_BASE+1.
    upper = read(close + 32, 4)
    load = read(close + 40, 4)
    if (int.from_bytes(upper, 'little') & 0xFFFF0000 != 0x3C020000
            or int.from_bytes(load, 'little') & 0xFFFF0000 != 0x8C430000
            or read(close + 44, 4) != packed(0xA0641C7E)):
        raise RuntimeError("Native skin save sequence changed")

    entry, request = arena + 0x100, arena + 0x1F0
    words = []
    exits = []

    def guard(register):
        exits.append(len(words))
        words.extend([m.bne(register, m.ZERO, 0), m.NOP])

    words += [m.lui(m.T0, (menu + 0x8000) >> 16), m.lw(m.T1, menu & 65535, m.T0)]
    guard(m.T1)
    words += [m.lw(m.T1, (menu + 4) & 65535, m.T0)]
    guard(m.T1)
    words += [*m.li32(m.T0, LoaderGate.STATE), m.lw(m.T1, 0, m.T0), m.xori(m.T1, m.T1, 6)]
    guard(m.T1)
    words += [*m.li32(m.T0, request), m.lbu(m.A0, 0, m.T0), m.sltiu(m.T1, m.A0, model_count)]
    exits.append(len(words))
    words += [m.beq(m.T1, m.ZERO, 0), m.NOP,
              m.addiu(m.SP, m.SP, -16), m.sd(m.RA, 0, m.SP), m.sw(m.A0, 8, m.SP),
              m.addiu(m.T1, m.ZERO, 255), m.sb(m.T1, 0, m.T0),
              jump(begin), m.addiu(m.A1, m.ZERO, 1)]
    failed = len(words)
    words += [m.beq(m.V0, m.ZERO, 0), m.NOP, jump(finish), m.NOP]
    failed_finish = len(words)
    words += [m.beq(m.V0, m.ZERO, 0), m.NOP,
              int.from_bytes(upper, 'little'), int.from_bytes(load, 'little'),
              m.lw(m.A0, 8, m.SP), m.sb(m.A0, 0x1C7E, m.V1)]
    epilogue = len(words)
    words += [m.ld(m.RA, 0, m.SP), m.addiu(m.SP, m.SP, 16)]
    end = len(words)
    words += [m.jr(m.RA), m.NOP]
    for index in exits:
        words[index] |= end - index - 1
    for index in (failed, failed_finish):
        words[index] |= epilogue - index - 1
    payload = packed(*words)
    if len(payload) > request - entry:
        raise RuntimeError("Skin callback exceeds reserved storage")
    payload = payload.ljust(request - entry, b'\0') + b'\xff'
    plan = Plan(pine, [Patch(gate + 4, packed(0x1074000A), packed(m.NOP)),
                       Patch(entry, pine.read_bytes(entry, len(payload)), payload)])
    plan.mutable_data = ((request, 1),)
    plan.entry, plan.request = entry, request
    plan.begin, plan.finish = begin, finish
    plan.model_count = model_count
    return plan

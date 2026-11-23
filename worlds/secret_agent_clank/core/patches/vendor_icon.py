from importlib.resources import files

from ..symbols import require
from . import mips as m
from .asm import Patch, jump, packed, words


def prepare_vendor_icon(pine, symbols, arena):
    lookup, invalidate, pause = require(symbols, "GetIconTextureID__14DrawObjManagerUi",
                                       "aglPs2VramInvalidate__Fv", "g_PauseModeData")
    original = pine.read_bytes(lookup, 24)
    native = words(original)
    if (native[0] & 0xFFFF0000 != 0x3C030000 or native[1] != 0x000420C0
            or native[2] & 0xFFFF0000 != 0x24630000
            or native[3:] != [0x00641821, 0x03E00008, 0x8C620004]):
        raise ValueError("Native icon lookup changed")
    invalidation = words(pine.read_bytes(invalidate, 12))
    if (invalidation[0] & 0xFFFF0000 != 0x3C020000 or invalidation[1] != m.jr(m.RA)
            or invalidation[2] & 0xFFFF0000 != 0xAC400000):
        raise ValueError("Native VRAM invalidation changed")
    low = invalidation[2] & 65535
    cache = ((invalidation[0] & 65535) << 16) + (low - 65536 if low & 32768 else low)
    root = files(__package__.split(".core.")[0]).joinpath("icon")
    pixels = root.joinpath("archipelago-icon.indices").read_bytes() + root.joinpath("archipelago-icon.clut").read_bytes()
    if len(pixels) != 2048:
        raise ValueError("Unexpected AP icon asset size")
    source = arena.allocate(pixels)
    backup = arena.allocate(bytes(2048))
    state = arena.allocate(bytes(8))
    code, labels, branches = [], {}, []

    def emit(*instructions):
        code.extend(instructions)

    def label(name):
        labels[name] = len(code)

    def branch(instruction, target):
        branches.append((len(code), target))
        emit(instruction, m.NOP)

    def copy_words(name):
        # t1 = source, t2 = destination; preserve state, desired mode and v0.
        emit(m.addiu(m.T3, m.ZERO, 512))
        label(name)
        emit(m.lw(m.T5, 0, m.T1), m.sw(m.T5, 0, m.T2),
             m.addiu(m.T1, m.T1, 4), m.addiu(m.T2, m.T2, 4), m.addiu(m.T3, m.T3, -1))
        branch(m.bne(m.T3, m.ZERO, 0), name)

    emit(m.addiu(m.T0, m.ZERO, 73))
    branch(m.bne(m.A0, m.T0, 0), "vanilla")
    emit(*native[:4], native[5])
    branch(m.beq(m.V0, m.ZERO, 0), "return")
    emit(*m.li32(m.T0, state), *m.li32(m.T1, pause + 12), m.lw(m.T1, 0, m.T1),
         m.xori(m.T2, m.T1, 8), m.sltiu(m.T2, m.T2, 1),
         m.xori(m.T4, m.T1, 16), m.sltiu(m.T4, m.T4, 1), m.or_(m.T4, m.T4, m.T2),
         m.lw(m.T1, 0, m.T0))
    branch(m.beq(m.V0, m.T1, 0), "known")
    branch(m.beq(m.T4, m.ZERO, 0), "return")
    emit(m.lw(m.T2, 0x34, m.V0), *m.li32(m.T3, 0x00200020))
    branch(m.bne(m.T2, m.T3, 0), "return")
    emit(m.lw(m.T1, 0x58, m.V0), m.lw(m.T2, 0x98, m.V0), m.addiu(m.T3, m.T1, 1024))
    branch(m.bne(m.T2, m.T3, 0), "return")
    emit(*m.li32(m.T3, 0x100000), m.sltu(m.T2, m.T1, m.T3))
    branch(m.bne(m.T2, m.ZERO, 0), "return")
    emit(*m.li32(m.T3, 0x1FFF801), m.sltu(m.T2, m.T1, m.T3))
    branch(m.beq(m.T2, m.ZERO, 0), "return")
    emit(*m.li32(m.T2, backup))
    copy_words("backup_loop")
    emit(m.sw(m.V0, 0, m.T0), m.sw(m.ZERO, 4, m.T0))
    label("known")
    emit(m.lw(m.T1, 4, m.T0))
    branch(m.beq(m.T1, m.T4, 0), "return")
    emit(*m.li32(m.T1, backup))
    branch(m.beq(m.T4, m.ZERO, 0), "copy")
    emit(*m.li32(m.T1, source))
    label("copy")
    emit(m.lw(m.T2, 0x58, m.V0))
    copy_words("copy_loop")
    emit(m.sw(m.T4, 4, m.T0), *m.li32(m.T0, cache), m.sw(m.ZERO, 0, m.T0))
    label("return")
    emit(m.jr(m.RA), m.NOP)
    label("vanilla")
    emit(*native[:2], jump(lookup + 8), m.NOP)
    for site, target in branches:
        code[site] |= (labels[target] - site - 1) & 65535
    entry = arena.allocate(packed(code))
    return [Patch(lookup, original[:8], packed([jump(entry), m.NOP]))]

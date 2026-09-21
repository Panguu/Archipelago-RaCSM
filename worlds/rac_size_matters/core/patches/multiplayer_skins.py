"""US multiplayer skins in the single-player menu.

The SP hero allocation is 0x89000 bytes. Bound its primary-file reads to
0x70000 (retail's largest model is 0x60a00), reserving the unused tail for
menu rows, descriptors, code, and a promoted LOD command list. MP LOD0 is a
placeholder; promotion must translate LOD1's reduced bone indices back to
the full animation skeleton. Merely replacing the LOD pointer distorts limbs.
"""
import struct

from . import mips as m
from .asm import Patch, j, jump, packed
from .plan import Plan

NAMES = ("Ratchet", "Snowman", "HotBot", "Qwark", "Ninja", "Training Bot",
         "Nurse", "Technomite", "Dan", "Low Rider Ratchet", "Samurai Ratchet",
         "Kangaroo Ratchet", "Tuxedo Ratchet")
COUNT = 7 + len(NAMES)
MCP = 0x1F4A740
SP_TABLE = 0x1EDCC10
MP_TABLE = 0x1EDCCB8
PRIMARY_LIMIT = 0x70000


class _Code:
    def __init__(self):
        self.words, self.labels, self.branches = [], {}, []

    def emit(self, *words):
        self.words.extend(words)

    def label(self, name):
        self.labels[name] = len(self.words)

    def branch(self, opcode, name, delay=0):
        self.branches.append((len(self.words), name))
        self.emit(opcode, delay)

    def pack(self):
        words = self.words.copy()
        for index, name in self.branches:
            words[index] |= (self.labels[name] - index - 1) & 0xFFFF
        return packed(*words)


def promoted_commands(commands, mapping):
    """Reference implementation used to validate the game-thread converter."""
    if len(commands) % 4 or not commands or len(commands) > 0x1000:
        raise ValueError("Invalid LOD command length")
    inverse = {}
    for full, reduced in enumerate(mapping):
        inverse.setdefault(reduced, full)
    words = list(struct.unpack("<%dI" % (len(commands) // 4), commands))
    if words[-1] != 0xFE000000:
        raise ValueError("Missing LOD terminator")
    for index, word in enumerate(words):
        if word >> 24 in (0xFA, 0xFB):
            if word & 0xFFFF not in inverse:
                raise ValueError("LOD bone has no full-skeleton mapping")
            words[index] = (word & 0xFFFF0000) | inverse[word & 0xFFFF]
    return packed(*words)


def prepare(pine, *, code_start, code, skin):
    """Prepare only while the level loader is held, or skin functions are idle."""
    if pine.get_game_id() != "SCUS-97615":
        raise RuntimeError("Multiplayer skins require US Size Matters")
    buffer = pine.read_int32(MCP + 0x2DC)
    if not 0x100000 <= buffer <= 0x1E00000 - 0x89000 or buffer & 15:
        raise RuntimeError("Single-player hero buffer is not allocated")
    edits = []

    def read(address, size):
        offset = address - code_start
        if not 0 <= offset <= len(code) - size:
            raise RuntimeError("Skin function outside loaded module")
        return code[offset:offset + size]

    def word(address):
        return struct.unpack("<I", read(address, 4))[0]

    def require(address, expected):
        if read(address, len(expected)) != expected:
            raise RuntimeError(f"Multiplayer skin signature changed at {address:#x}")

    def patch(address, expected, replacement):
        require(address, expected)
        edits.append(Patch(address, expected, replacement))

    def call(address):
        value = word(address)
        if value >> 26 != 3:
            raise RuntimeError("Skin loader call changed")
        return (value & 0x3FFFFFF) << 2

    def ptr(upper, lower):
        return ((word(upper) & 65535) << 16) + struct.unpack("<h", read(lower, 2))[0]

    def redirect_ptr(upper, lower, old, new):
        if word(upper) >> 26 != 15 or word(lower) >> 26 != 9 or ptr(upper, lower) != old:
            raise RuntimeError("Skin table reference changed")
        patch(upper, packed(word(upper)), packed((word(upper) & 0xFFFF0000) | ((new + 0x8000) >> 16)))
        patch(lower, packed(word(lower)), packed((word(lower) & 0xFFFF0000) | (new & 65535)))

    # These allocations are disjoint from the model, promoted geometry,
    # two texture buffers, and one another.
    rows, menu_table, descriptors = buffer + 0x72000, buffer + 0x74000, buffer + 0x74800
    finish, stock_finish, owned, label, add_row = (buffer + x for x in
                                                 (0x75000, 0x75700, 0x75800, 0x75840, 0x75880))
    strings = buffer + 0x75A00
    begin, end = skin.begin, skin.finish
    gate = skin.edits[0].address - 4
    old_menu = ptr(gate - 0x1C, gate - 0x18)
    original_rows = read(old_menu, 7 * 16)
    if [struct.unpack_from("<I", original_rows, i * 16)[0] for i in range(7)] != [0, 1, 2, 6, 3, 5, 4]:
        raise RuntimeError("Unexpected single-player skin table")
    sp = pine.read_bytes(SP_TABLE, 7 * 24)
    mp = pine.read_bytes(MP_TABLE, 13 * 64)
    if [struct.unpack_from("<I", mp, i * 64)[0] for i in range(13)] != [26, 50, 8, 16, 9, 56, 12, 53, 3, 25, 28, 19, 31]:
        raise RuntimeError("Unexpected multiplayer asset table")
    menu_data, descriptor_data, text = bytearray(original_rows), bytearray(sp), bytearray()
    for index, name in enumerate(NAMES):
        source = struct.unpack_from("<16I", mp, index * 64)
        model = 7 + index
        menu_data += packed(model, 0, strings + len(text), model)
        text += ("Multiplayer Ratchet" if index == 0 else name).encode("ascii") + b"\0"
        descriptor_data += packed(source[0], source[1], source[5], source[9], 0, 0)
    if len(text) > 0x400 or COUNT * 0xE4 > 0x2000:
        raise RuntimeError("Multiplayer skin storage overflow")
    for hi, lo in [(-0x93C, -0x934), (-0x814, -0x810), (-0x738, -0x730),
                   (-0x34C, -0x348), (-0x1C0, -0x1B8), (-0x1C, -0x18),
                   (0x84, 0x9C), (0xBD4, 0xBD8)]:
        redirect_ptr(gate + hi, gate + lo, old_menu, menu_table)
    for offset, expected, replacement in [
        (-0x378, 0x2E620FB9, 0x2E620000 | (0xFB2 + COUNT)),
        (-0x1C8, 0x2CA20007, 0x2CA20000 | COUNT),
        (0x34, 0x2E220007, 0x2E220000 | COUNT),
        (0x144, 0x2E220007, 0x2E220000 | COUNT),
        (0x170, 0x2E220007, 0x2E220000 | COUNT),
        (-0xB4, 0x24061000, 0x24062000),
    ]:
        patch(gate + offset, packed(expected), packed(replacement))
    old_rows = ptr(gate - 0xBC, gate - 0x88)
    redirect_ptr(gate - 0xBC, gate - 0x88, old_rows, rows)
    # The normal loader also handles the extended descriptor table. Never
    # allow a primary PAK read to overwrite the storage reserved above.
    for offset, expected, replacement in [(0x3C, 0x3C120008, 0x3C120007),
                                          (0x4C, 0x36524000, 0x36520000),
                                          (0xD8, 0x3C070008, 0x3C070007),
                                          (0xE8, 0x34E74000, 0x34E70000)]:
        patch(begin + offset, packed(expected), packed(replacement))
    # Preserve the texture offset: native begin uses S2 for both its limit
    # and the secondary texture address. Supply the original 0x84000 offset.
    require(begin + 0x78, packed(0x0292B021))
    # At this point S6=buffer+0x70000. Redirect the cache-flush call through
    # a trampoline that corrects S6 while preserving the native delay slot.
    begin_fix = buffer + 0x75900
    patch(begin + 0x7C, packed(jump(0x1E92A20)), packed(jump(begin_fix)))

    size, load, asset = call(begin + 0xAC), call(begin + 0xE4), call(end + 0xB4)
    pak = ptr(begin + 0xA4, begin + 0xB0)
    pending = ptr(end + 4, end + 16)
    changed = ptr(end + 0x98, end + 0xA4)
    apply = ptr(end + 0x9C, end + 0xA8)
    is_owned = call(gate - 0x91C)
    for offset in (-0x91C, -0x728, 0x108):
        patch(gate + offset, packed(jump(is_owned)), packed(jump(owned)))
    gettext = call(gate - 0x8A8)
    patch(gate - 0x8A8, packed(jump(gettext)), packed(jump(label)))
    native_add = call(gate + 0x28)
    patch(gate + 0x28, packed(jump(native_add)), packed(jump(add_row)))

    c = _Code()
    c.emit(*m.li32(m.T0, pending), m.lw(m.T1, 0, m.T0), m.sltiu(m.T2, m.T1, 7))
    c.branch(m.beq(m.T2, m.ZERO, 0), "mp")
    c.emit(j(stock_finish), 0)
    c.label("mp")
    c.emit(m.sltiu(m.T2, m.T1, COUNT))
    c.branch(m.beq(m.T2, m.ZERO, 0), "invalid")
    c.emit(m.addiu(m.SP, m.SP, -0x90), m.sd(m.RA, 0x80, m.SP))
    for index, reg in enumerate((m.S0, m.S1, m.S2, m.S3, m.S4)):
        c.emit(m.sd(reg, 0x50 + index * 8, m.SP))
    c.emit(m.move(m.S4, m.T1), *m.li32(m.S0, buffer),
           m.addiu(m.T0, m.T1, -7), m.sll(m.T0, m.T0, 6),
           *m.li32(m.S1, MP_TABLE), m.addu(m.S1, m.S1, m.T0),
           *m.li32(m.T0, changed), m.lbu(m.S2, 0, m.T0),
           *m.li32(m.T0, apply), m.lbu(m.S3, 0, m.T0),
           m.lw(m.A1, 12, m.S1))
    c.branch(m.beq(m.A1, m.ZERO, 0), "textures")
    c.branch(m.beq(m.S2, m.ZERO, 0), "textures")
    c.emit(*m.li32(m.A0, pak), jump(size), 0, m.sltiu(m.T0, m.V0, 0x5001))
    c.branch(m.beq(m.T0, m.ZERO, 0), "failed")
    c.emit(m.sw(m.V0, 0x3C, m.S1), *m.li32(m.A0, pak), m.lw(m.A1, 12, m.S1),
           *m.li32(m.A2, buffer + 0x7F000), jump(load), m.addiu(m.A3, m.ZERO, 0x5000))
    c.label("textures")
    c.emit(m.sw(m.ZERO, 0, m.SP), m.sw(m.ZERO, 4, m.SP),
           *m.li32(m.T0, 0xB9C25B73), m.sw(m.T0, 8, m.SP),
           m.sw(m.ZERO, 12, m.SP), m.sw(m.ZERO, 16, m.SP),
           *m.li32(m.T0, 0xB51670D1), m.sw(m.T0, 20, m.SP),
           m.sll(m.T0, m.S4, 1), m.addu(m.T0, m.T0, m.S4), m.sll(m.T0, m.T0, 3),
           *m.li32(m.T1, descriptors), m.addu(m.T0, m.T0, m.T1),
           *m.li32(m.T1, buffer + 0x84000), m.sw(m.T1, 24, m.SP),
           m.lw(m.T1, 20, m.T0), m.sw(m.T1, 28, m.SP),
           m.lw(m.T1, 12, m.T0), m.sw(m.T1, 32, m.SP),
           m.lw(m.T0, 12, m.S1), m.addiu(m.A2, m.ZERO, 3))
    c.branch(m.beq(m.T0, m.ZERO, 0), "load")
    c.emit(*m.li32(m.T0, buffer + 0x7F000), m.sw(m.T0, 36, m.SP),
           m.lw(m.T0, 0x3C, m.S1), m.sw(m.T0, 40, m.SP),
           m.lw(m.T0, 0x2C, m.S1), m.sw(m.T0, 44, m.SP), m.addiu(m.A2, m.ZERO, 4))
    c.label("load")
    c.emit(m.move(m.A0, m.ZERO), m.move(m.A1, m.S0), m.move(m.A3, m.SP),
           m.move(m.T0, m.S2), m.move(m.T1, m.S3), jump(asset), m.move(m.T2, m.ZERO))
    c.branch(m.beq(m.V0, m.ZERO, 0), "failed")
    c.branch(m.beq(m.S2, m.ZERO, 0), "done")
    # Promote a copy; altering LOD1 itself would break distant rendering.
    c.emit(m.lw(m.T0, 0x1C, m.S0), m.lw(m.T1, 0x1C, m.T0),
           m.lw(m.T2, 0x20, m.T0), m.lw(m.T3, 0x24, m.S0),
           m.lw(m.T3, 0x14, m.T3), m.lw(m.T4, 0x20, m.S0), m.lw(m.T4, 4, m.T4),
           *m.li32(m.T5, buffer + PRIMARY_LIMIT), *m.li32(m.T6, buffer + PRIMARY_LIMIT + 0x1000))
    c.label("copy")
    c.emit(m.sltu(m.V0, m.T1, m.T2))
    c.branch(m.beq(m.V0, m.ZERO, 0), "failed")
    c.emit(m.sltu(m.V0, m.T5, m.T6))
    c.branch(m.beq(m.V0, m.ZERO, 0), "failed")
    c.emit(m.lw(m.T7, 0, m.T1), m.srl(m.T8, m.T7, 24), m.addiu(m.T9, m.ZERO, 0xFA))
    c.branch(m.beq(m.T8, m.T9, 0), "bone")
    c.emit(m.addiu(m.T9, m.ZERO, 0xFB))
    c.branch(m.bne(m.T8, m.T9, 0), "write")
    c.label("bone")
    c.emit(m.andi(m.A0, m.T7, 0xFFFF), m.move(m.A1, m.ZERO))
    c.label("search")
    c.emit(m.sltu(m.V0, m.A1, m.T4))
    c.branch(m.beq(m.V0, m.ZERO, 0), "failed")
    c.emit(m.addu(m.A2, m.T3, m.A1), m.lbu(m.A2, 0, m.A2))
    c.branch(m.beq(m.A2, m.A0, 0), "found")
    c.branch(m.beq(m.ZERO, m.ZERO, 0), "search", m.addiu(m.A1, m.A1, 1))
    c.label("found")
    c.emit(m.srl(m.T7, m.T7, 16), m.sll(m.T7, m.T7, 16), m.or_(m.T7, m.T7, m.A1))
    c.label("write")
    c.emit(m.sw(m.T7, 0, m.T5), m.addiu(m.T1, m.T1, 4), m.addiu(m.T5, m.T5, 4),
           m.addiu(m.T9, m.ZERO, 0xFE))
    c.branch(m.bne(m.T8, m.T9, 0), "copy")
    c.emit(*m.li32(m.T1, buffer + PRIMARY_LIMIT), m.sw(m.T1, 0x18, m.T0))
    c.label("done")
    c.emit(*m.li32(m.T0, MCP), m.sb(m.S4, 0x2E0, m.T0),
           *m.li32(m.T0, pending), m.addiu(m.T1, m.ZERO, -1), m.sw(m.T1, 0, m.T0),
           m.addiu(m.V0, m.ZERO, 1))
    c.branch(m.beq(m.ZERO, m.ZERO, 0), "return")
    c.label("failed")
    c.emit(m.move(m.V0, m.ZERO))
    c.label("return")
    for index, reg in enumerate((m.S0, m.S1, m.S2, m.S3, m.S4)):
        c.emit(m.ld(reg, 0x50 + index * 8, m.SP))
    c.emit(m.ld(m.RA, 0x80, m.SP), m.jr(m.RA), m.addiu(m.SP, m.SP, 0x90))
    c.label("invalid")
    c.emit(m.jr(m.RA), m.move(m.V0, m.ZERO))
    finish_code = c.pack()
    if len(finish_code) > stock_finish - finish:
        raise RuntimeError("Multiplayer loader exceeds reserved code storage")
    owned_code = packed(m.sltiu(m.T0, m.A1, 7), m.bne(m.T0, m.ZERO, 3), 0,
                        m.jr(m.RA), m.sltiu(m.V0, m.A1, COUNT), j(is_owned), 0)
    label_code = packed(m.sltiu(m.T0, m.A0, 0x1000), m.bne(m.T0, m.ZERO, 3), 0,
                        m.jr(m.RA), m.move(m.V0, m.A0), j(gettext), 0)
    add_code = packed(m.sltiu(m.T2, m.A2, 7), m.xori(m.T2, m.T2, 1), j(native_add), 0)
    fix_code = packed(m.addiu(m.SP, m.SP, -16), m.sd(m.RA, 0, m.SP),
                      *m.li32(m.T0, 0x84000), m.addu(m.S6, m.S4, m.T0),
                      # Each level rebuilds the extended descriptors with empty
                      # size caches, even when the resident loaded id survives.
                      # Force a fresh MP read before finish uploads its textures.
                      m.sltiu(m.T0, m.S3, 7), m.bne(m.T0, m.ZERO, 2), 0,
                      m.addiu(m.S0, m.ZERO, -1),
                      jump(0x1E92A20), 0, m.ld(m.RA, 0, m.SP), m.jr(m.RA), m.addiu(m.SP, m.SP, 16))
    data_edits = []
    for address, payload in [(rows, bytes(0x2000)), (menu_table, bytes(menu_data)),
                             (descriptors, bytes(descriptor_data)), (finish, finish_code),
                             (stock_finish, read(end, 0xE8)), (owned, owned_code),
                             (label, label_code), (add_row, add_code), (begin_fix, fix_code), (strings, bytes(text))]:
        data_edits.append(Patch(address, pine.read_bytes(address, len(payload)), payload))
    table_pointer = MCP + 0x2D4
    previous_table = pine.read_int32(table_pointer)
    if previous_table not in (SP_TABLE, descriptors):
        raise RuntimeError("Hero descriptor pointer already modified")
    data_edits.append(Patch(table_pointer, packed(previous_table), packed(descriptors)))
    # Install the initialized storage before publishing any entry points.
    patch(end, read(end, 8), packed(j(finish), 0))
    plan = Plan(pine, data_edits + edits)
    plan.mutable_data = ((rows, 0x2000), (descriptors, len(descriptor_data)))
    plan.buffer, plan.count, plan.finish = buffer, COUNT, finish
    plan.rows, plan.table, plan.descriptors = rows, menu_table, descriptors
    plan.promoted = buffer + PRIMARY_LIMIT
    return plan

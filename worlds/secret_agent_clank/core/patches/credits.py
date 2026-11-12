import hashlib

from . import mips as m
from .asm import Patch, packed, jump


TABLE_OFFSET = 0x21F450
ENTRY_SIZE = 64
RETAIL_COUNT = 113
LINES = (
    "Archipelago",
    "Developers",
    "Pangu    Amondo",
    # The retail subtitle uses half-size glyphs. Twenty leading blank cells
    # shift its visible centre five full-size characters right, under Amondo.
    "                    Trap",
    "Special Thanks",
    "ImJustATester",
    "The Knowledge GOAT of SAC and SM",
    "SomeLazyGamer",
    "Poptracker and tester",
    "Taoshi",
    "rac3 dev i stole everything from",
)
TABLE_SHA256 = "6da77475719f65d7686df98c0b3cce774cc69b90fd92140267914786746baf8b"
LINE_TICKS = 180
# Emit paired descriptions on the next update, then hold the complete pair.
SUBTITLE_ROWS = frozenset((3, 6, 8, 10))
ROW_TICKS = tuple(0 if i + 1 in SUBTITLE_ROWS else LINE_TICKS for i in range(len(LINES)))


def prepare_schedule(base, loaded, arena):
    """Extend the authored rail's end event before allowing its movie handoff.

    The retail rail emits exactly 113 lines. Increasing the selector's modulus
    alone cannot schedule more waves. Retain native name/subtitle configurations
    and emit paired rows from the normal gameplay update, with a reading
    interval after each group (including the last), then resume retail completion.
    """
    # Name configuration, argument, active, timer, subtitle configuration.
    state = arena.allocate(bytes(20))
    styles = arena.allocate(packed([value for i in range(len(LINES))
                                   for value in (int(i in SUBTITLE_ROWS), ROW_TICKS[i])]))
    reset = arena.allocate(packed([
        *m.li32(m.T0, state), *(m.sw(m.ZERO, offset, m.T0) for offset in (0, 4, 8, 12, 16)),
        m.addiu(m.SP, m.SP, -0x20), m.swc1(m.F20, 0x10, m.SP),
        jump(base + 0xBD900), m.NOP,
    ]))
    # Preserve the authored Dan Johnson / Lead Modeler name and subtitle
    # configurations, instead of using the final single-line heading for both.
    capture = arena.allocate(packed([
        *m.li32(m.T0, state), *m.li32(m.T1, base + 0x21EA18),
        m.lw(m.T1, 0, m.T1), m.addiu(m.T2, m.ZERO, 110),
        m.bne(m.T1, m.T2, 2), m.NOP, m.sw(m.A0, 16, m.T0),
        m.addiu(m.T2, m.ZERO, 109), m.beq(m.T1, m.T2, 4), m.NOP,
        m.lw(m.T2, 0, m.T0), m.bne(m.T2, m.ZERO, 3), m.NOP,
        m.sw(m.A0, 0, m.T0), m.sw(m.A1, 4, m.T0),
        m.addiu(m.SP, m.SP, -0x170), m.sd(m.S5, 0xE8, m.SP),
        jump(base + 0xBB4F8), m.NOP,
    ]))
    begin = arena.allocate(packed([
        *m.li32(m.T0, state), m.lw(m.T1, 0, m.T0),
        m.bne(m.T1, m.ZERO, 3), m.NOP,
        jump(base + 0xBA650), m.NOP,  # no captured wave: retain retail behavior
        m.addiu(m.T1, m.ZERO, 1), m.sw(m.T1, 8, m.T0),
        m.addiu(m.T1, m.ZERO, LINE_TICKS),
        m.jr(m.RA), m.sw(m.T1, 12, m.T0),
    ]))
    code, labels, branches = [], {}, []

    def emit(*instructions):
        code.extend(instructions)

    def branch(rs, rt, label):
        branches.append((len(code), rs, rt, label))
        emit(0, m.NOP)

    emit(m.addiu(m.SP, m.SP, -16), m.sd(m.RA, 8, m.SP), m.sd(m.S0, 0, m.SP),
         *m.li32(m.S0, state), m.lw(m.T0, 8, m.S0))
    branch(m.T0, m.ZERO, 'done')
    emit(m.lw(m.T0, 12, m.S0))
    branch(m.T0, m.ZERO, 'emit')
    emit(m.addiu(m.T0, m.T0, -1), m.sw(m.T0, 12, m.S0))
    branch(m.ZERO, m.ZERO, 'done')
    labels['emit'] = len(code)
    emit(*m.li32(m.T0, base + 0x21EA18), m.lw(m.T0, 0, m.T0),
         m.sltiu(m.T0, m.T0, RETAIL_COUNT + len(LINES) - 1))
    branch(m.T0, m.ZERO, 'complete')
    emit(*m.li32(m.T0, base + 0x21EA18), m.lw(m.T0, 0, m.T0),
         m.addiu(m.T0, m.T0, 1 - RETAIL_COUNT),
         m.lw(m.A0, 0, m.S0), m.addiu(m.T1, m.ZERO, LINE_TICKS),
         m.sw(m.T1, 12, m.S0), m.sltiu(m.T1, m.T0, len(LINES)))
    # A particle-budget skip can leave the retail selector behind its rail.
    # Finish those rows with the name style, without indexing before styles.
    branch(m.T1, m.ZERO, 'spawn')
    emit(m.sll(m.T0, m.T0, 3),
         *m.li32(m.T1, styles), m.addu(m.T1, m.T1, m.T0),
         m.lw(m.T0, 4, m.T1), m.sw(m.T0, 12, m.S0),
         m.lw(m.T0, 0, m.T1), m.lw(m.A0, 0, m.S0))
    branch(m.T0, m.ZERO, 'spawn')
    emit(m.lw(m.T0, 16, m.S0))
    branch(m.T0, m.ZERO, 'spawn')
    emit(m.move(m.A0, m.T0))
    labels['spawn'] = len(code)
    emit(m.lw(m.A1, 4, m.S0), jump(base + 0xBB4F0, link=True), m.NOP)
    branch(m.ZERO, m.ZERO, 'done')
    labels['complete'] = len(code)
    emit(m.sw(m.ZERO, 8, m.S0), jump(base + 0xBA650, link=True), m.NOP)
    labels['done'] = len(code)
    emit(m.ld(m.S0, 0, m.SP), m.ld(m.RA, 8, m.SP), m.addiu(m.SP, m.SP, 16),
         jump(base + 0xBAA18), m.NOP)
    for at, rs, rt, label in branches:
        code[at] = m.beq(rs, rt, labels[label] - at - 1)
    tick = arena.allocate(packed(code))
    edits = (
        (0xBD8F8, packed([m.addiu(m.SP, m.SP, -0x20), m.swc1(m.F20, 0x10, m.SP)]),
         packed([jump(reset), m.NOP])),
        (0xBB4F0, packed([m.addiu(m.SP, m.SP, -0x170), m.sd(m.S5, 0xE8, m.SP)]),
         packed([jump(capture), m.NOP])),
        (0xBBC28, packed([jump(base + 0xBA650, link=True)]), packed([jump(begin, link=True)])),
        (0xBDF2C, packed([jump(base + 0xBAA18, link=True)]), packed([jump(tick, link=True)])),
    )
    patches = []
    for offset, before, after in edits:
        if loaded[offset:offset + len(before)] != before:
            raise ValueError(f"Interactive credits scheduler differs at {offset:#x}")
        patches.append(Patch(base + offset, before, after))
    return patches


def prepare_credits(base, loaded, symbols, arena):
    table = loaded[TABLE_OFFSET:TABLE_OFFSET + RETAIL_COUNT * ENTRY_SIZE]
    if hashlib.sha256(table).hexdigest() != TABLE_SHA256:
        raise ValueError("Unexpected interactive credits table")
    if (symbols.get("GCS_SetupTextTables__Fv") != base + 0xBB380
            or symbols.get("GCS_StartWaveLetter__FPC14GCS_WaveConfigi") != base + 0xBB4F0):
        raise ValueError("Unexpected interactive credits routines")
    entries = []
    for line in LINES:
        encoded = line.encode("ascii")
        if not encoded or len(encoded) >= ENTRY_SIZE:
            raise ValueError("Interactive credit does not fit its native entry")
        entries.append(encoded.ljust(ENTRY_SIZE, b"\0"))
    target = arena.allocate(table + b"".join(entries))
    original = base + TABLE_OFFSET
    count = RETAIL_COUNT + len(entries)
    edits = (
        # Setup uppercases every entry in place; the wave selector must use
        # this same writable table and wrap after the appended entries.
        (0xBB43C, m.lui(m.V0, (original + 0x8000) >> 16), m.lui(m.V0, (target + 0x8000) >> 16)),
        (0xBB444, m.addiu(m.S2, m.V0, original), m.addiu(m.S2, m.V0, target)),
        (0xBB598, m.lui(m.A0, (original + 0x8000) >> 16), m.lui(m.A0, (target + 0x8000) >> 16)),
        (0xBB59C, m.addiu(m.A0, m.A0, original), m.addiu(m.A0, m.A0, target)),
        (0xBB4C4, m.sltiu(m.V0, m.S1, RETAIL_COUNT), m.sltiu(m.V0, m.S1, count)),
        (0xBB590, m.addiu(m.V1, m.ZERO, RETAIL_COUNT), m.addiu(m.V1, m.ZERO, count)),
    )
    patches = []
    for offset, before, after in edits:
        expected = packed([before])
        if loaded[offset:offset + 4] != expected:
            raise ValueError(f"Interactive credits instruction differs at {offset:#x}")
        patches.append(Patch(base + offset, expected, packed([after])))
    return patches + prepare_schedule(base, loaded, arena)

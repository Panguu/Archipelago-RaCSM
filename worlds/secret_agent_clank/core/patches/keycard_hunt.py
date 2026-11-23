"""The Treehouse door checks AP keycards instead of the pickup save flags."""
from ...constants import KEYCARD_ITEMS
from ..global_flags import GlobalFlags
from ..symbols import require
from . import mips as m
from ..batch_io import read_blocks
from .asm import Patch, jump, packed, words


class KeycardHunt:
    def __init__(self, pine):
        self.pine = pine
        self.enabled = False
        self.mask = 0
        self.table = self.entry = self.pointer_address = self.enable_address = None
        self.code = b""

    def receive(self, names):
        self.mask = sum(1 << bit for name, bit in KEYCARD_ITEMS.items() if name in names)

    @staticmethod
    def routine(table, getter, original):
        # Only flag AA (the door) reads the keycard table. Every other flag runs
        # the original getter. Only uses registers the getter already clobbers.
        return packed([
            m.addiu(m.V0, m.ZERO, 0xAA), m.bne(m.A0, m.V0, 6),
            m.andi(m.A1, m.A1, 0xFF), *m.li32(m.V0, table),
            m.lbu(m.V0, 0, m.V0), m.jr(m.RA), m.and_(m.V0, m.V0, m.A1),
            words(original)[0], jump(getter + 8), words(original)[1],
        ])

    def prepare(self, symbols, module, arena):
        self.table = self.entry = self.pointer_address = self.enable_address = None
        if module != 31:
            return []
        flags = GlobalFlags(self.pine)
        if not flags.bind(symbols):
            raise RuntimeError("Keycard Hunt flag getter layout changed")
        getter = require(symbols, "GLOBAL_GetFlag__FUiUc")
        original = self.pine.read_bytes(getter, 8)
        self.table = arena.allocate(bytes(8))
        self.enable_address = self.table + 4
        # With Keycard Hunt off, skip to the original getter at the end of the routine.
        code = [*m.li32(m.V0, self.enable_address), m.lw(m.V0, 0, m.V0),
                m.beq(m.V0, m.ZERO, 9), m.NOP,
                *words(self.routine(self.table, getter, original))]
        self.code = packed(code)
        self.entry = arena.allocate(self.code)
        self.pointer_address = flags.pointer_address
        return [Patch(getter, original, packed([jump(self.entry), m.NOP]))]

    def sync(self):
        if self.table is None:
            return
        module, loading, code = read_blocks(self.pine, [(0x206328, 4), (0x206324, 4), (self.entry, len(self.code))])
        if module != packed([31]) or loading != packed([0xFFFFFFFF]):
            return
        if code != self.code:
            raise RuntimeError("Keycard Hunt code changed")
        self.pine.write_int32(self.table, self.mask)
        self.pine.write_int32(self.enable_address, int(self.enabled))

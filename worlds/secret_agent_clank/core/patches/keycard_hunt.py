"""Use AP ownership at the Treehouse door without writing pickup save bits."""
from ...constants import KEYCARD_ITEMS
from ..global_flags import GlobalFlags
from ..symbols import require
from . import mips as m
from ..batch_io import read_blocks
from .asm import Patch, capture, jump, packed, words
from .gain_storage import GainStorage
from .storage import plan_storage


class KeycardHunt:
    def __init__(self, pine):
        self.pine = pine
        self.enabled = False
        self.mask = 0
        self.table = self.entry = self.pointer_address = None
        self.code = b""
        self.enable_address = None

    def receive(self, names):
        self.mask = sum(1 << bit for name, bit in KEYCARD_ITEMS.items() if name in names)

    @staticmethod
    def routine(table, getter, original):
        # Only flag AA is redirected. Other flags execute the original getter.
        # Use only registers the original leaf function already clobbers.
        return packed([
            m.addiu(m.V0, m.ZERO, 0xAA), m.bne(m.A0, m.V0, 6),
            m.andi(m.A1, m.A1, 0xFF), *m.li32(m.V0, table),
            m.lbu(m.V0, 0, m.V0), m.jr(m.RA), m.and_(m.V0, m.V0, m.A1),
            words(original)[0], jump(getter + 8), words(original)[1],
        ])

    def prepare(self, symbols, hooks, module):
        self.enable_address = None
        self.table = self.entry = self.pointer_address = None
        if not self.enabled or module != 31:
            return []
        flags = GlobalFlags(self.pine)
        if not flags.bind(symbols):
            raise RuntimeError("Keycard Hunt flag getter layout changed")
        getter = require(symbols, "GLOBAL_GetFlag__FUiUc")
        original = self.pine.read_bytes(getter, 8)
        ranges = list(hooks.extra_ranges)
        edits = []
        sizes = [44, 4]
        addresses = plan_storage(ranges, hooks.patches, sizes)
        if addresses is None and not hooks.gain_storage_prepared:
            guards, extra = GainStorage(self.pine).prepare(symbols)
            edits.extend(guards)
            ranges.extend(extra)
            hooks.extra_ranges.extend(extra)
            hooks.gain_storage_prepared = True
            addresses = plan_storage(ranges, hooks.patches + edits, sizes)
        if addresses is None:
            raise RuntimeError("Insufficient verified storage for Keycard Hunt")
        entry, table = addresses
        code = self.routine(table, getter, original)
        edits.extend(capture(self.pine, [(entry, code), (table, packed([self.mask]))]))
        edits.append(Patch(getter, original, packed([jump(entry), m.NOP])))
        self.entry, self.table, self.code = entry, table, code
        self.pointer_address = flags.pointer_address
        return edits

    def prepare_permanent(self, symbols, module, arena):
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
        # Keep the complete vanilla path when this run has no Keycard Hunt.
        code = [*m.li32(m.V0, self.enable_address), m.lw(m.V0, 0, m.V0),
                m.beq(m.V0, m.ZERO, 9), m.NOP]
        redirected = words(self.routine(self.table, getter, original))
        # The original routine's last three words are its vanilla trampoline.
        code += redirected
        self.code = packed(code)
        self.entry = arena.allocate(self.code)
        self.pointer_address = flags.pointer_address
        return [Patch(getter, original, packed([jump(self.entry), m.NOP]))]

    def sync(self):
        if (not self.enabled and self.enable_address is None) or self.table is None:
            return
        module, loading, code = read_blocks(self.pine, [(0x206328, 4), (0x206324, 4), (self.entry, len(self.code))])
        if module != packed([31]) or loading != packed([0xFFFFFFFF]):
            return
        if code != self.code:
            raise RuntimeError("Keycard Hunt code changed")
        self.pine.write_int32(self.table, self.mask)
        if self.enable_address is not None:
            self.pine.write_int32(self.enable_address, int(self.enabled))

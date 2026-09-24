"""AP ownership snapshot applied before native object initialization."""
from . import mips as m
from .asm import jump, packed
from .patch import Patch


class Entitlements(Patch):
    def __init__(self, pine):
        super().__init__(pine)
        self.table = None

    def prepare(self, *, address, table, gadget_base, fallback):
        self.address = self.table = None
        self.original = self.replacement = b""
        for value, size in ((address, 80), (table, 41),
                            (gadget_base, 40 * 0x74), (fallback, 4)):
            if type(value) is not int or not 0x100000 <= value <= 0x2000000 - size:
                raise ValueError("Invalid entitlement routine address")
        if address % 4 or gadget_base % 4 or fallback % 4:
            raise ValueError("Unaligned entitlement routine address")
        code = self._build_routine(table, gadget_base, fallback)
        if address < table + 41 and table < address + len(code):
            raise ValueError("Entitlement table overlaps its routine")
        original = self.pine.read_bytes(address, len(code))
        if len(original) != len(code):
            raise RuntimeError("Incomplete original entitlement routine read")
        self.address, self.table = address, table
        self.original, self.replacement = original, code
        return self

    def read(self):
        """Return the ownership snapshot and object-init invocation count."""
        if self.table is None:
            raise RuntimeError("Prepare Entitlements before reading")
        data = self.pine.read_bytes(self.table, 41)
        if len(data) != 41:
            raise RuntimeError("Incomplete entitlement table read")
        return {"flags": data[:40], "initializations": data[40]}

    @staticmethod
    def _build_routine(table, gadget_base, fallback):
        """Apply managed AP ownership immediately before native object init."""
        owned = gadget_base + 0x70
        return packed([
            *m.li32(m.T0, table),                          # t0 = table
            *m.li32(m.T1, owned),                          # t1 = owned
            m.addiu(m.T2, m.T0, 0x28),                      # t2 = table end
            m.lbu(m.T3, 0, m.T0),                           # loop: t3 = *t0
            m.beq(m.T3, m.ZERO, 2), m.addiu(m.T3, m.T3, -1),  # unmanaged skips store; delay subtracts 1
            m.sw(m.T3, 0, m.T1),                            # *t1 = t3
            m.addiu(m.T0, m.T0, 1),                         # next table slot
            m.bne(m.T0, m.T2, -6), m.addiu(m.T1, m.T1, 0x74),  # loop; delay advances GadgetData slot
            m.lbu(m.T3, 0, m.T0), m.addiu(m.T3, m.T3, 1), m.sb(m.T3, 0, m.T0),  # invocation counter
            jump(fallback), 0,
        ])

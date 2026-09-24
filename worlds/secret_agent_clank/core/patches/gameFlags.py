"""Native pickup/vendor location flags, separate from gameplay ownership."""
from . import mips as m
from .asm import jump, packed
from .patch import Patch


class GameFlags(Patch):
    SLOT_COUNT = 40
    UNMANAGED = 0
    UNCHECKED = 1
    CHECKED = 2

    def __init__(self, pine):
        super().__init__(pine)
        self.table = None
        self.record = None

    def prepare(self, *, address, table, fallback, record):
        """Prepare a routine in storage already verified by the enclosing plan."""
        self.address = self.table = self.record = None
        self.original = self.replacement = b""
        if type(record) is not bool:
            raise ValueError("record must be a boolean")
        for name, value, size, aligned in (
                ("address", address, 64, True), ("table", table, self.SLOT_COUNT, False),
                ("fallback", fallback, 4, True)):
            if (type(value) is not int or not 0x100000 <= value <= 0x2000000 - size
                    or (aligned and value % 4)):
                raise ValueError(f"Invalid {name} address")
        replacement = self._build_routine(table, fallback, record=record)
        if address < table + self.SLOT_COUNT and table < address + len(replacement):
            raise ValueError("Flag table overlaps the routine")
        original = self.pine.read_bytes(address, len(replacement))
        if len(original) != len(replacement):
            raise RuntimeError("Incomplete original routine read")
        self.address, self.table, self.record = address, table, record
        self.original, self.replacement = original, replacement
        return self

    def read(self):
        """Return all 40 raw flag bytes; this never confirms AP locations."""
        if self.table is None:
            raise RuntimeError("Prepare GameFlags before reading its table")
        result = self.pine.read_bytes(self.table, self.SLOT_COUNT)
        if len(result) != self.SLOT_COUNT:
            raise RuntimeError("Incomplete flag table read")
        return result

    @staticmethod
    def _build_routine(table, fallback, *, record):
        """a0=gadget id."""
        code = [
            m.sltiu(m.V0, m.A0, 40),           # v0 = (a0 < 40) ? 1 : 0
            0, 0,                              # [1]=beq placeholder, [2]=its delay slot
            *m.li32(m.T0, table),              # t0 = table
            m.addu(m.T0, m.T0, m.A0),          # t0 = table + gadget id
            m.lbu(m.V0, 0, m.T0),              # v0 = *t0 (current flag byte)
            0, 0,                              # [7]=beq placeholder, [8]=its delay slot
        ]
        code += ([m.addiu(m.V0, m.ZERO, 2), m.sb(m.V0, 0, m.T0), m.jr(m.RA), 0] if record
                 else [m.addiu(m.V0, m.V0, -1), m.jr(m.RA), 0])
        target = len(code)
        code += [jump(fallback), 0]
        for i in (1, 7):
            code[i] = m.beq(m.V0, m.ZERO, target - i - 1)
        return packed(code)

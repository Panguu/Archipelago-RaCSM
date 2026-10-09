"""Count the successful End(StealthTakeDown) path per case, not the transient enemy list."""
import struct

from ..constants.stealth import STEALTH_MAX_PER_CASE, stealth_location_name
from .patches import mips as m
from .patches.asm import Patch, jump, packed

END = "End__15StealthTakeDown"
KILL = "CLANKSTEALTH_GiveStealthKill__FP4Mobyf"


class StealthState:
    def __init__(self, pine):
        self.pine = pine
        self.cases = {}
        self.counts = {}
        self.loaded = False
        self.binding = None
        self.on_count = lambda counts: None

    def configure(self, cases, *, reset=False):
        """`cases`: slot data's case -> number of stealth checks."""
        if not isinstance(cases, dict) or any(
                type(count) is not int or not 0 <= count <= STEALTH_MAX_PER_CASE for count in cases.values()):
            raise ValueError("Invalid stealth_cases slot data")
        self.cases = dict(cases)
        self.loaded = False
        if reset:
            self.counts = {}
            self.binding = None

    def load(self, counts):
        if not isinstance(counts, dict) or any(
                type(count) is not int or not 0 <= count <= STEALTH_MAX_PER_CASE for count in counts.values()):
            raise ValueError("Invalid stored stealth counts")
        for case, count in counts.items():
            self.counts[case] = max(self.counts.get(case, 0), count)
        self.loaded = True

    @staticmethod
    def wrapper(counter, target):
        # At this call site all these registers are caller-saved; preserve
        # a0, f12 and ra for the original native call via a tail jump.
        return packed([m.lui(m.T0, (counter + 0x8000) >> 16), m.lw(m.T1, counter & 65535, m.T0),
                       m.sltiu(m.T2, m.T1, STEALTH_MAX_PER_CASE), m.beq(m.T2, m.ZERO, 2),
                       m.addiu(m.T1, m.T1, 1), m.sw(m.T1, counter & 65535, m.T0),
                       jump(target), 0])

    def prepare(self, symbols, allocate, case):
        """Hook the success path for `case`, the Clank case this module plays."""
        self.binding = None
        if case not in self.cases:
            return []
        end, kill = symbols.get(END), symbols.get(KILL)
        if end is None and kill is None:
            return []  # Modules without Clank's takedown implementation.
        if end is None or kill is None:
            raise RuntimeError("Incomplete native stealth exports")
        # Both failure flags bypass the success-only call at End + 0xB0.
        expected = {0x3C: 0x92220015, 0x40: 0x54400005,
                    0x48: 0x9222002C, 0x4C: 0x10400014,
                    0x98: 0x10000012, 0xA8: 0x3C013F80,
                    0xAC: 0x44816000, 0xB0: jump(kill, link=True),
                    0xB4: 0x8E040010}
        if any(self.pine.read_int32(end + offset) != word for offset, word in expected.items()):
            raise RuntimeError("Native successful stealth takedown path changed")
        counter = allocate(struct.pack("<I", self.counts.get(case, 0)))
        code = self.wrapper(counter, kill)
        address = allocate(code)
        site = end + 0xB0
        original = packed([expected[0xB0]])
        replacement = packed([jump(address, link=True)])
        self.binding = (case, counter, site, replacement, address, code)
        return [Patch(site, original, replacement)]

    def poll(self):
        if not self.cases or not self.loaded or self.binding is None:
            return
        case, counter, site, replacement, address, code = self.binding
        # Safe even during loading: never interpret a replaced module as a
        # counter. Poll before the loader installs the next module's plan.
        if (self.pine.read_bytes(site, 4) != replacement
                or self.pine.read_bytes(address, len(code)) != code):
            self.binding = None
            return
        count = self.pine.read_int32(counter)
        if not 0 <= count <= STEALTH_MAX_PER_CASE:
            raise RuntimeError("Invalid native stealth count")
        known = self.counts.get(case, 0)
        if count > known:
            self.counts[case] = count
            self.on_count({case: count})
        elif count < known:
            # Restore server progress after a reload/savestate rollback.
            self.pine.batch_write_int32([(counter, known)])

    def checks(self):
        if not self.loaded:
            return ()
        return tuple(stealth_location_name(case, n) for case, total in self.cases.items()
                     for n in range(1, min(total, self.counts.get(case, 0)) + 1))

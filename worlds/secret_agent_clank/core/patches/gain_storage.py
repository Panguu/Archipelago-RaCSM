from ..batch_io import read_blocks
from ..symbols import require
from . import mips as m
from .asm import Patch, packed, jump
from .debug_stubs import DEBUG_STUBS
from .mips import jr
from .patch import PatchSet

RETURN_IMMEDIATELY = packed([jr(m.RA), m.NOP])


class GainStorage(PatchSet):
    def __init__(self, pine):
        super().__init__(pine)
        self.ranges = []

    def prepare(self, symbols):
        self.patches = []
        self.ranges = []
        pine = self.pine
        # Each stub's prologue spills its own arguments below SP (64-bit GPRs
        # via sd, the VEC3-taking stub's floats via swc1) then falls straight
        # into an unconditional return -- dead code the game never re-enters,
        # confirmed by this exact signature before any hook claims the space.
        edits, ranges = [], []
        addresses = [require(symbols, stub.symbol) for stub in DEBUG_STUBS]
        current = read_blocks(pine, [(address, len(stub.signature)) for address, stub in zip(addresses, DEBUG_STUBS)])
        for stub, address, signature in zip(DEBUG_STUBS, addresses, current):
            if signature != stub.signature:
                raise RuntimeError(f"Gain storage stub layout changed: {stub.symbol}")
            edits.append(Patch(address, stub.signature[:len(RETURN_IMMEDIATELY)],
                               RETURN_IMMEDIATELY))
            ranges.append((address + len(RETURN_IMMEDIATELY), address + len(stub.signature)))

        # Check complete function extents, including the replacement entry.
        extents = sorted((edit.address, end) for edit, (_, end) in zip(edits, ranges))
        if any(end > next_start for (_, end), (next_start, _) in zip(extents, extents[1:])):
            raise RuntimeError("Gain storage stubs overlap")
        self.patches = edits
        self.ranges = ranges
        return edits, ranges

    def prepare_line(self, symbols):
        """Extra storage when the ordinary hook arenas cannot fit the plan.

        The retail VEC4 line stub copies vertices onto its own stack and sets
        a stack-local color. It submits no geometry and changes no game data.
        Validate every word, including the sole callee, before bypassing it.
        """
        address, color = require(symbols, "DEBUGDRAW_DrawLineSegment__FPC4VEC4T0Uib",
                                 "SetARGB__7ApeRGBAUi")
        color_code = packed([0x00051602, 0x00051A02, 0x00053402, 0xA0820003,
                             0xA0830001, 0xA0860000, 0x03E00008, 0xA0850002])
        code = packed([
            0x27BDFFC0, 0x0080102D, 0xFFBF0030, 0x00A0182D, 0x00C0282D,
            0x27A40020, 0xC4440008, 0xC4650008, 0xC4400000, 0xC4410004,
            0xC4620000, 0xC4630004, 0xE7A00010, 0xE7A10014, 0xE7A40018,
            0xE7A20020, 0xE7A30024, 0xE7A50028, 0x7BA20010, 0x7BA30020,
            0x7FA20000, jump(color, True), 0x7FA30010, 0xDFBF0030,
            0x03E00008, 0x27BD0040])
        if read_blocks(self.pine, [(address, len(code)), (color, len(color_code))]) != [code, color_code]:
            raise RuntimeError("Gain storage line stub layout changed")
        return ([Patch(address, code[:8], RETURN_IMMEDIATELY)],
                [(address + 8, address + len(code))])

"""Verified storage in retail debug-print stubs that already do nothing."""
from ..symbols import require
from . import mips as m
from .asm import Patch, packed
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
        for stub in DEBUG_STUBS:
            address = require(symbols, stub.symbol)
            if pine.read_bytes(address, len(stub.signature)) != stub.signature:
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

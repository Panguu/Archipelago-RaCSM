from ..batch_io import read_blocks
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
        # These debug print stubs only save their arguments and return, so
        # everything after an early return is free space.
        edits, ranges = [], []
        addresses = [require(symbols, stub.symbol) for stub in DEBUG_STUBS]
        current = read_blocks(pine, [(address, len(stub.signature)) for address, stub in zip(addresses, DEBUG_STUBS)])
        for stub, address, signature in zip(DEBUG_STUBS, addresses, current):
            if signature != stub.signature:
                raise RuntimeError(f"Gain storage stub layout changed: {stub.symbol}")
            edits.append(Patch(address, stub.signature[:len(RETURN_IMMEDIATELY)],
                               RETURN_IMMEDIATELY))
            ranges.append((address + len(RETURN_IMMEDIATELY), address + len(stub.signature)))

        extents = sorted((edit.address, end) for edit, (_, end) in zip(edits, ranges))
        if any(end > next_start for (_, end), (next_start, _) in zip(extents, extents[1:])):
            raise RuntimeError("Gain storage stubs overlap")
        self.patches = edits
        self.ranges = ranges
        return edits, ranges

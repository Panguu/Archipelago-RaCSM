"""Arena win counters resolved from the native arena table and current save."""
import struct

from ...constants.ratchet_challenges import RATCHET_CHALLENGES, RATCHET_CHALLENGES_BY_CASE
from ..case_menu import CASE_LABELS, ee_pointer
from ..global_flags import GlobalFlags
from .case_events import CaseEventInventory


class RatchetChallengeInventory(CaseEventInventory):
    def __init__(self, pine):
        super().__init__(pine, RATCHET_CHALLENGES)
        self.flags = GlobalFlags(pine)
        self.indices = {}

    def invalidate(self):
        self.indices = {}
        self.flags.pointer_address = None

    def bind(self, symbols):
        self.invalidate()
        address = symbols.get("Arena_GetWinCount__FUiUi")
        getter = symbols.get("GLOBAL_GetFlag__FUiUc")
        if address is None or getter is None or not self.flags.bind(symbols):
            return False
        w = struct.unpack("<10I", self.pine.read_bytes(address, 40))
        if (w[:2] != (0x27BDFFF0, 0xFFBF0000) or w[2] >> 26 != 3
                or w[3:5] != (0, 0x0040202D)
                or w[5:] != (0x0C000000 | (getter >> 2), 0x240500FF,
                             0xDFBF0000, 0x03E00008, 0x27BD0010)):
            return False
        index_function = (w[2] & 0x03FFFFFF) << 2
        if not ee_pointer(index_function, 60):
            return False
        w = struct.unpack("<15I", self.pine.read_bytes(index_function, 60))
        if (w[:3] != (0x27BDFFF0, 0xFFB00000, 0xFFBF0008)
                or w[3] >> 26 != 3 or w[4] != 0x00A0802D
                or w[5] & 0xFFFF0000 != 0x3C030000 or w[6] != 0x00021140
                or w[7] & 0xFFFF0000 != 0x24630000
                or w[8:] != (0xDFBF0008, 0x00431021, 0x8C420010,
                              0x00501021, 0xDFB00000, 0x03E00008, 0x27BD0010)):
            return False
        low = w[7] & 0xFFFF
        table = ((w[5] & 0xFFFF) << 16) + (low - 0x10000 if low & 0x8000 else low)
        if not ee_pointer(table, 160):
            return False
        indices = {}
        for row in range(5):
            record = struct.unpack("<8I", self.pine.read_bytes(table + row * 32, 32))
            names = RATCHET_CHALLENGES_BY_CASE.get(CASE_LABELS.get(record[0]))
            if names is None or len(names) != 5 or not 0x54 <= record[4] <= 0x74:
                return False
            indices.update((name, record[4] + i) for i, name in enumerate(names))
        if len(indices) != 25 or len(set(indices.values())) != 25:
            return False
        self.indices = indices
        return True

    def get(self, entry):
        index = self.indices.get(str(entry))
        value = self.flags.read(index) if index is not None else None
        return value is not None and value[0] > 0

    def sync(self):
        # Saved wins must be reported on connection/level entry, not baselined away.
        pass

    def check(self):
        return [str(entry) for entry in self.entries
                if not self.completed[str(entry)] and self.get(entry)]

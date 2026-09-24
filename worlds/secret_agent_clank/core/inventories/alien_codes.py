"""Persistent Alien Code bits, independently read from native save flags."""
import struct

from ...constants.alien_codes import ALIEN_CODE_MODULES, ALIEN_CODES_BY_CASE
from ..global_flags import GlobalFlags


class AlienCodeInventory:
    def __init__(self, pine):
        self.pine = pine
        self.flags = GlobalFlags(pine)
        self.reported = set()
        self.valid = False
        self.found = set()

    def bind(self, symbols):
        self.valid = False
        if not self.flags.bind(symbols):
            return False
        get_count = symbols.get("GLOBALVARS_GetTotalAlienCodeCount__FUi")
        if get_count is None:
            return False
        w = struct.unpack("<7I", self.pine.read_bytes(get_count, 28))
        if (w[0] != 0x2484FFFF or w[1] & 0xFFFF0000 != 0x3C020000
                or w[2] & 0xFFFF0000 != 0x24420000
                or w[3:] != (0x00042080, 0x00822021, 0x03E00008, 0x8C820000)):
            return False
        low = w[2] & 0xFFFF
        table = ((w[1] & 0xFFFF) << 16) + (low - 0x10000 if low & 0x8000 else low)
        counts = struct.unpack("<30I", self.pine.read_bytes(table, 120))
        if {i + 1: n for i, n in enumerate(counts) if n} != dict.fromkeys(ALIEN_CODE_MODULES.values(), 3):
            return False
        self.valid = True
        return True

    def sync(self):
        # Do not baseline away a collection completed during level startup.
        pass

    def sync_from_ap(self, checked):
        self.reported.update(checked)

    def check(self):
        if not self.valid:
            return []
        data = self.flags.read(0x38, 15)
        if data is None:
            return []
        self.found = set()
        for case, module in ALIEN_CODE_MODULES.items():
            for index, name in enumerate(ALIEN_CODES_BY_CASE[case]):
                if data[(module - 1) // 2] & (1 << (((module - 1) & 1) * 4 + index)):
                    self.found.add(name)
        return sorted(self.found - self.reported)

    def confirm(self, name: str) -> None:
        """Mark a name check() returned as successfully delivered to AP -- see core/case_events.py's CaseEventInventory.confirm() for why this must wait for Core.send_location(name) to return True rather than happening unconditionally inside check()."""
        self.reported.add(name)

    @property
    def all_found(self):
        return self.valid and len(self.found) == 27

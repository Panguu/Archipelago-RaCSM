"""Native keycard bits and the actual keycard door opening in Treehouse."""
import struct

from ...constants.keycards import KEYCARDS
from ..global_flags import GlobalFlags


class KeycardInventory:
    def __init__(self, pine):
        self.pine = pine
        self.flags = GlobalFlags(pine)
        self.reported = set()
        self.found = set()
        self.door_opened = False
        self.chalice_collected = False
        self.root_pointer = None
        self.door_type = None
        self._door = None

    def bind(self, symbols):
        self.flags.bind(symbols)
        self.root_pointer = self.door_type = None
        self._door = None
        if self.pine.read_int32(0x206328) != 31:
            return
        find = symbols.get("MOBY_FindMoby__FUi")
        self.door_type = symbols.get("UberDoor_typeInfo")
        if find is None or self.door_type is None:
            return
        w = struct.unpack("<5I", self.pine.read_bytes(find, 20))
        if (w[0] & 0xFFFF0000 != 0x3C050000 or w[1] & 0xFFFF0000 != 0x8CA30000
                or w[2:] != (0x8C620048, 0x8C630044, 0x000211C0)):
            return
        low = w[1] & 0xFFFF
        self.root_pointer = ((w[0] & 0xFFFF) << 16) + (low - 0x10000 if low & 0x8000 else low)

    def sync_from_ap(self, checked):
        self.reported.update(checked)

    def _door_is_open(self):
        p = self.pine
        if self.root_pointer is None or p.read_int32(0x206328) != 31:
            return False
        if self._door is not None:
            address, kind, pv, runtime = self._door
            if (p.read_int32(address + 0x40) == kind and p.read_int32(kind + 0x10) == self.door_type
                    and p.read_int32(address + 0x54) == pv and p.read_int32(address + 0x58) == runtime
                    and p.read_int8(pv + 0x32) == 1):
                return p.read_int8(address + 0x45) == 3 and p.read_int8(runtime + 0x34) == 0
            self._door = None
        root = p.read_int32(self.root_pointer)
        if not 0x100000 <= root <= 0x1FFFFB0:
            return False
        start, count = struct.unpack("<2I", p.read_bytes(root + 0x44, 8))
        if not 0 < count <= 20000 or not 0x100000 <= start <= 0x2000000 - count * 0x80:
            return False
        matches = []
        type_cache = {}
        # Read in bounded PINE messages; find only the door configured to need cards.
        for offset in range(0, count * 0x80, 0x10000):
            data = p.read_bytes(start + offset, min(0x10000, count * 0x80 - offset))
            for i in range(0, len(data), 0x80):
                kind, = struct.unpack_from("<I", data, i + 0x40)
                if not 0x100000 <= kind <= 0x1FFFFB0:
                    continue
                if kind not in type_cache:
                    type_cache[kind] = p.read_int32(kind + 0x10)
                if type_cache[kind] != self.door_type:
                    continue
                pv, runtime = struct.unpack_from("<2I", data, i + 0x54)
                if not (0x100000 <= pv <= 0x1FFFFA0 and 0x100000 <= runtime <= 0x1FFFFC8):
                    continue
                if p.read_int8(pv + 0x32) == 1:
                    matches.append((start + offset + i, kind, pv, runtime))
        if len(matches) == 1:
            self._door = matches[0]
            return self._door_is_open()
        return False

    def check(self):
        value = self.flags.read(0xAA)
        if value is None:
            return []
        self.found = {str(entry) for bit, entry in enumerate(KEYCARDS) if value[0] & (1 << bit)}
        chalice = self.flags.read(0xCB)
        self.chalice_collected = chalice is not None and chalice[0] != 0
        if value[0] == 7 and self._door_is_open():
            self.door_opened = True
        return sorted(self.found - self.reported)

    def confirm(self, name: str) -> None:
        """Mark a name check() returned as successfully delivered to AP -- see core/case_events.py's CaseEventInventory.confirm() for why this must wait for Core.send_location(name) to return True rather than happening unconditionally inside check()."""
        self.reported.add(name)

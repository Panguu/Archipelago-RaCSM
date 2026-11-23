import struct
from collections import Counter


def read_module_counts(pine, function_address):
    """Decode a GLOBALVARS_GetTotal*Count routine's per-module count table.

    Returns {module: count} for every module with a non-zero count, or None if the
    routine's instructions don't match the expected native layout.
    """
    w = struct.unpack("<7I", pine.read_bytes(function_address, 28))
    if (w[0] != 0x2484FFFF or w[1] & 0xFFFF0000 != 0x3C020000
            or w[2] & 0xFFFF0000 != 0x24420000
            or w[3:] != (0x00042080, 0x00822021, 0x03E00008, 0x8C820000)):
        return None
    low = w[2] & 0xFFFF
    table = ((w[1] & 0xFFFF) << 16) + (low - 0x10000 if low & 0x8000 else low)
    counts = struct.unpack("<30I", pine.read_bytes(table, 120))
    return {i + 1: n for i, n in enumerate(counts) if n}


def module_counts(flags):
    return dict(Counter(module for module, _ in flags.values()))


def module_bit(data, module, bit):
    """Read bit `bit` of a one-based module's nibble in a packed per-module flag array."""
    return bool(data[(module - 1) // 2] & (1 << (((module - 1) & 1) * 4 + bit)))


class GlobalFlags:
    def __init__(self, pine):
        self.pine = pine
        self.pointer_address = None

    def bind(self, symbols):
        self.pointer_address = None
        address = symbols.get('GLOBAL_GetFlag__FUiUc')
        if address is None:
            return False
        w = struct.unpack('<7I', self.pine.read_bytes(address, 28))
        if (w[0] & 0xFFFF0000 != 0x3C020000 or w[1] != 0x30A500FF
                or w[2] & 0xFFFF0000 != 0x8C430000
                or w[3:] != (0x00641821, 0x906204E0, 0x03E00008, 0x00451024)):
            return False
        low = w[2] & 0xFFFF
        self.pointer_address = ((w[0] & 0xFFFF) << 16) + (low - 0x10000 if low & 0x8000 else low)
        return True

    def read(self, index, count=1):
        if self.pointer_address is None:
            return None
        base = self.pine.read_int32(self.pointer_address)
        if not 0x100000 <= base <= 0x2000000 - 0x4E0 - index - count:
            return None
        result = self.pine.read_bytes(base + 0x4E0 + index, count)
        if self.pine.read_int32(self.pointer_address) != base:
            return None
        return result

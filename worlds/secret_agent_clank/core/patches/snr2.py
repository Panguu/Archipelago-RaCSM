"""The local stream format follows SCUS-97623's loader at 0x175930; imported
relocations follow 0x175AC8 and the relocation writer at 0x175010.
This is a build/verification tool, not a PINE runtime memory writer.
"""
from dataclasses import dataclass
import struct


class InvalidModule(ValueError):
    pass


def word(data, offset):
    if offset < 0 or offset + 4 > len(data):
        raise InvalidModule(f"Word outside module: {offset:#x}")
    return struct.unpack_from("<I", data, offset)[0]


@dataclass(frozen=True)
class Symbol:
    name: str
    value: int
    kind: int
    name_hash: int


@dataclass(frozen=True)
class Relocation:
    offset: int
    kind: int
    symbol: int | None = None
    addend: int = 0


class SNR2Module:
    def __init__(self, data: bytes):
        self.data = data
        if len(data) < 128 or data[:4] != b"SNR2":
            raise InvalidModule("Expected SNR2 level module")
        if word(data, 40) != 128 or word(data, 44) != len(data):
            raise InvalidModule("Unsupported SNR2 header/size")
        self.symbols = self._symbols()
        self.local_relocations = self._local_relocations()
        self.import_relocations = self._import_relocations()
        sites = [r.offset for r in self.local_relocations + self.import_relocations]
        if len(sites) != len(set(sites)):
            raise InvalidModule("Duplicate relocation site")

    def _symbols(self):
        offset, count = word(self.data, 12), word(self.data, 16)
        if offset % 4 or offset < 128 or offset + count * 12 > len(self.data):
            raise InvalidModule("Symbol table outside module")
        result = []
        for index in range(count):
            name, value, tag = struct.unpack_from("<III", self.data, offset + index * 12)
            if not 128 <= name < offset:
                raise InvalidModule("Symbol name outside string table")
            end = self.data.find(b"\0", name, offset)
            if end < 0:
                raise InvalidModule("Unterminated symbol name")
            try:
                decoded = self.data[name:end].decode("ascii")
            except UnicodeDecodeError as exc:
                raise InvalidModule("Non-ASCII symbol name") from exc
            kind = (tag >> 16) & 255
            if kind > 4 or tag >> 24:
                raise InvalidModule("Unsupported symbol kind/status")
            if kind in (2, 3) and value >= len(self.data):
                raise InvalidModule("Export outside module")
            result.append(Symbol(decoded, value, kind, tag & 65535))
        return tuple(result)

    def _local_relocations(self):
        cursor = word(self.data, 52)
        if cursor == 0:
            self.local_stream_end = 128
            return ()
        if not 128 <= cursor < len(self.data):
            raise InvalidModule("Local relocation stream outside module")
        result = []
        address = 0
        while cursor < len(self.data):
            command = self.data[cursor]
            cursor += 1
            kind, delta = command & 3, command & 252
            if delta:
                address += delta
            else:
                address = word(self.data, cursor)
                cursor += 4
                if not address:
                    self.local_stream_end = cursor
                    return tuple(result)
            if address % 4 or not 128 <= address <= len(self.data) - 4:
                raise InvalidModule("Invalid local relocation site")
            result.append(Relocation(address, kind))
        raise InvalidModule("Unterminated local relocation stream")

    def _import_relocations(self):
        offset, count = word(self.data, 4), word(self.data, 8)
        if offset % 4 or offset < 128 or offset + count * 12 > len(self.data):
            raise InvalidModule("Import relocation table outside module")
        result = []
        for index in range(count):
            site, info, addend = struct.unpack_from("<III", self.data, offset + index * 12)
            kind, symbol = info & 255, info >> 8
            if site % 4 or not 128 <= site <= len(self.data) - 4:
                raise InvalidModule("Invalid import relocation site")
            if kind not in (1, 2, 4, 5, 6, 119) or symbol >= len(self.symbols):
                raise InvalidModule("Unsupported import relocation")
            result.append(Relocation(site, kind, symbol, addend))
        return tuple(result)

    def relocate(self, base: int, imports: dict[str, int]) -> tuple[bytes, dict[str, int]]:
        if base < 0x100000 or base % 16 or base + len(self.data) > 0x2000000:
            raise InvalidModule("Invalid EE module load address")
        result = bytearray(self.data)
        values = []
        exports = {}
        for symbol in self.symbols:
            if symbol.kind in (2, 3, 4):
                value = base + symbol.value if symbol.kind != 4 else symbol.value
                if symbol.name in exports and exports[symbol.name] != value:
                    raise InvalidModule(f"Ambiguous export: {symbol.name}")
                exports[symbol.name] = value
            elif symbol.kind == 1:
                if symbol.name not in imports:
                    raise InvalidModule(f"Unresolved import: {symbol.name}")
                value = imports[symbol.name]
            else:
                # The native kind-0 record is module-relative too (the null
                # symbol is used as a base anchor by relocation producers).
                value = base + symbol.value
            values.append(value)
        next_low = {}
        low = None
        for relocation in reversed(self.local_relocations):
            if relocation.kind == 0:
                low = relocation.offset
            elif relocation.kind == 1:
                next_low[relocation.offset] = low
        for relocation in self.local_relocations:
            offset, kind = relocation.offset, relocation.kind
            original = word(self.data, offset)
            if kind == 0:
                self._write(result, offset, 6, base + (original & 65535))
            elif kind == 1:
                # Native loader looks ahead to the next LO16 without consuming
                # intervening records. Several HI16s may share one LO16.
                low = next_low[offset]
                if low is None:
                    raise InvalidModule("HI16 without following LO16")
                signed = struct.unpack_from("<h", self.data, low)[0]
                value = ((original & 65535) << 16) + signed + base
                self._write(result, offset, 5, value)
            elif kind == 2:
                self._write(result, offset, 4, ((original & 0x3FFFFFF) << 2) + base)
            else:
                self._write(result, offset, 2, original + base)
        for relocation in self.import_relocations:
            self._write(result, relocation.offset, relocation.kind,
                        values[relocation.symbol] + relocation.addend)
        return bytes(result), exports

    @staticmethod
    def _write(result, offset, kind, value):
        value &= 0xFFFFFFFF
        original = word(result, offset)
        if kind in (4, 5, 6) and original & 0xFC00003F == 13:
            raise InvalidModule("Loader would reject BREAK relocation")
        if kind == 2:
            struct.pack_into("<I", result, offset, value)
        elif kind == 4:
            struct.pack_into("<I", result, offset, original & 0xFC000000 | (value >> 2) & 0x3FFFFFF)
        elif kind == 119:
            struct.pack_into("<I", result, offset, original & 0xFFE0003F | (value << 3) & 0x1FFFC0)
        else:
            half = (value + 0x8000) >> 16 if kind == 5 else value
            struct.pack_into("<H", result, offset, half & 65535)


def resident_exports(executable: bytes) -> dict[str, int]:
    """Read the resident USA ELF's registered SNR2 symbol table."""
    if executable[:7] != b"\x7fELF\x01\x01\x01":
        raise InvalidModule("Expected little-endian ELF32")
    phoff = word(executable, 28)
    size, count = struct.unpack_from("<HH", executable, 42)
    segments = []
    for index in range(count):
        start = phoff + index * size
        if size < 32 or start + 32 > len(executable):
            raise InvalidModule("Truncated ELF program headers")
        kind, offset, address, _, filesz, memsz, _, _ = struct.unpack_from("<8I", executable, start)
        if kind == 1:
            if offset + filesz > len(executable) or memsz < filesz:
                raise InvalidModule("Invalid ELF load segment")
            segments.append((address, offset, filesz))

    def file_offset(address, length=4):
        for base, offset, size in segments:
            if base <= address and address + length <= base + size:
                return offset + address - base
        raise InvalidModule(f"Resident address not file-backed: {address:#x}")

    root = word(executable, file_offset(0x1CD7DC))
    header = file_offset(root, 60)
    if executable[header:header + 4] != b"SNR2":
        raise InvalidModule("Resident SNR2 table changed")
    table, count = word(executable, header + 12), word(executable, header + 16)
    start = file_offset(table, count * 12)
    result = {}
    for index in range(count):
        name, value, tag = struct.unpack_from("<III", executable, start + index * 12)
        if (tag >> 16) & 255 not in (2, 3, 4):
            continue
        name_start = file_offset(name)
        end = executable.find(b"\0", name_start, name_start + 1024)
        if end < 0:
            raise InvalidModule("Unterminated resident symbol name")
        decoded = executable[name_start:end].decode("ascii")
        if decoded in result and result[decoded] != value:
            raise InvalidModule(f"Ambiguous resident export: {decoded}")
        result[decoded] = value
    return result

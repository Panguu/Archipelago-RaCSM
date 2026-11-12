"""Writes patches into a level module and rebuilds its relocation tables, so the
game's loader relocates the new code wherever the module loads.
"""
from dataclasses import dataclass
import struct

from .snr2 import InvalidModule, Relocation, SNR2Module, word


@dataclass(frozen=True)
class Fixup:
    offset: int  # Relative to the replacement bytes.
    kind: int  # Native relocation kind: 2=word, 4=jump, 5=HI16, 6=LO16.
    symbol: str
    addend: int = 0


@dataclass(frozen=True)
class ModuleEdit:
    offset: int
    original: bytes
    replacement: bytes
    fixups: tuple[Fixup, ...] = ()


def encode_local_relocations(relocations: tuple[Relocation, ...]) -> bytes:
    result = bytearray()
    previous = 0
    for relocation in relocations:
        offset, kind = relocation.offset, relocation.kind
        if offset < 128 or offset % 4 or kind not in (0, 1, 2, 3) or relocation.symbol is not None:
            raise InvalidModule("Invalid local relocation")
        delta = offset - previous
        if 0 < delta <= 252:
            result.append(delta | kind)
        else:
            result.append(kind)
            result.extend(struct.pack("<I", offset))
        previous = offset
    return bytes(result + bytes(5))


def compile_module(data: bytes, edits: tuple[ModuleEdit, ...], *, arena_start: int | None = None) -> bytes:
    """Apply the edits and write fresh relocation tables at the end of the file.
    Existing code and symbols don't move.
    """
    module = SNR2Module(data)
    if not edits:
        raise InvalidModule("Empty module patch plan")
    edits = tuple(sorted(edits, key=lambda edit: edit.offset))
    metadata_start = min(word(data, 4), word(data, 12), word(data, 52) or len(data))
    if arena_start is not None:
        # The arena has to be empty space after all the original tables.
        metadata_end = max(word(data, 4) + word(data, 8) * 12,
                           word(data, 12) + word(data, 16) * 12,
                           module.local_stream_end)
        if (arena_start % 16 or arena_start < metadata_end or arena_start >= len(data)
                or any(data[arena_start:])):
            raise InvalidModule("Invalid module extension arena")
    end = 128
    for edit in edits:
        if (not edit.original or len(edit.original) != len(edit.replacement)
                or edit.offset % 4 or len(edit.original) % 4 or edit.offset < end
                or not (edit.offset + len(edit.original) <= metadata_start
                        or (arena_start is not None and edit.offset >= arena_start
                            and edit.offset + len(edit.original) <= len(data)))):
            raise InvalidModule("Unaligned, overlapping or out-of-code module edit")
        if data[edit.offset:edit.offset + len(edit.original)] != edit.original:
            raise InvalidModule(f"Original module bytes differ at {edit.offset:#x}")
        end = edit.offset + len(edit.original)
    removed = {offset for edit in edits for offset in range(edit.offset, edit.offset + len(edit.original), 4)}
    imports = [r for r in module.import_relocations if r.offset not in removed]
    locals_ = []
    # A kept HI16 whose LO16 was replaced would pair with the wrong LO16 in the
    # compressed stream, so turn those into explicit symbol+addend relocations.
    anchor = next((i for i, s in enumerate(module.symbols) if s.kind in (2, 3)), None)
    low = None
    pairs = {}
    for r in reversed(module.local_relocations):
        if r.kind == 0:
            low = r.offset
        elif r.kind == 1:
            if low is None:
                raise InvalidModule("HI16 without LO16")
            pairs[r.offset] = low
    for r in module.local_relocations:
        if r.offset in removed:
            continue
        if r.kind == 1 and pairs[r.offset] in removed:
            if anchor is None:
                raise InvalidModule("No local symbol for surviving HI16")
            target = ((word(data, r.offset) & 65535) << 16) + struct.unpack_from("<h", data, pairs[r.offset])[0]
            imports.append(Relocation(r.offset, 5, anchor, target - module.symbols[anchor].value))
        else:
            locals_.append(r)
    symbols = {}
    for index, symbol in enumerate(module.symbols):
        if symbol.name in symbols:
            raise InvalidModule(f"Duplicate symbol: {symbol.name}")
        symbols[symbol.name] = index
    result = bytearray(data)
    for edit in edits:
        result[edit.offset:edit.offset + len(edit.replacement)] = edit.replacement
        for fixup in edit.fixups:
            if (fixup.kind not in (2, 4, 5, 6) or fixup.offset % 4 or fixup.offset < 0
                    or fixup.offset + 4 > len(edit.replacement) or fixup.symbol not in symbols
                    or not -(1 << 31) <= fixup.addend < (1 << 32)):
                raise InvalidModule("Invalid replacement fixup")
            imports.append(Relocation(edit.offset + fixup.offset, fixup.kind, symbols[fixup.symbol], fixup.addend))
    sites = [r.offset for r in imports] + [r.offset for r in locals_]
    if len(sites) != len(set(sites)):
        raise InvalidModule("Duplicate replacement fixup")
    result.extend(bytes((-len(result)) % 4))
    import_start = len(result)
    for r in imports:
        result.extend(struct.pack("<III", r.offset, (r.symbol << 8) | r.kind, r.addend & 0xFFFFFFFF))
    local_start = len(result)
    result.extend(encode_local_relocations(tuple(locals_)))
    struct.pack_into("<II", result, 4, import_start, len(imports))
    struct.pack_into("<I", result, 44, len(result))
    struct.pack_into("<I", result, 52, local_start)
    # Retail SNR2 keeps the same stream pointer in both header fields.
    if word(data, 56) == word(data, 52):
        struct.pack_into("<I", result, 56, local_start)
    elif word(data, 56):
        raise InvalidModule("Unsupported secondary relocation stream")
    SNR2Module(bytes(result))  # parse it to catch a malformed result
    return bytes(result)

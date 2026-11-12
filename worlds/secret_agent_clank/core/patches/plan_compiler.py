"""Turns a patch builder into a relocatable level module.

The builder runs at a few load addresses. Every word that changes with the
address has to match one of the loader's relocation types (WORD, J26, HI16,
LO16) and becomes a fixup. The result is then checked at more addresses.
"""

from .module_compiler import Fixup, ModuleEdit, compile_module
from .snr2 import InvalidModule, SNR2Module, word


REFERENCE_BASE = 0x400000
CHECK_BASES = (0x328B00, 0x508010, 0x617FF0, 0x708000, 0x80FFF0, 0x900010)


def compile_native_plan(data: bytes, imports: dict[str, int], builder, *, arena_start: int | None = None) -> bytes:
    """builder(base, relocated_bytes, exports) returns Patch records. It must give
    the same result every time, so nothing seed-specific can go in the code.
    """
    module = SNR2Module(data)
    anchors = [symbol for symbol in module.symbols if symbol.kind in (2, 3)]
    if not anchors:
        raise InvalidModule("No module-relative symbol anchor")
    anchor = anchors[0]
    plans = {}

    def plan(base):
        if base not in plans:
            loaded, exports = module.relocate(base, imports)
            patches = sorted(builder(base, loaded, exports), key=lambda patch: patch.address)
            records = []
            end = 128
            for patch in patches:
                offset = patch.address - base
                size = len(patch.original)
                if (offset < end or not size
                        or len(patch.replacement) != size or offset + size > len(data)
                        or loaded[offset:offset + size] != patch.original):
                    raise InvalidModule(f"Invalid/overlapping native patch at {offset:#x}, size {size}")
                # Text and byte flags can be unaligned, so widen to whole words
                # and merge edits that share a word.
                low, high = offset & ~3, (offset + size + 3) & ~3
                if high > len(loaded):
                    raise InvalidModule("Aligned native patch exceeds module")
                if records and low <= records[-1][0] + len(records[-1][1]):
                    start, block = records[-1]
                    block.extend(loaded[start + len(block):high])
                else:
                    start, block = low, bytearray(loaded[low:high])
                    records.append((start, block))
                block[offset - start:offset - start + size] = patch.replacement
                end = offset + size
            if not records:
                raise InvalidModule("Native builder produced no patches")
            plans[base] = tuple((offset, bytes(block)) for offset, block in records)
        records = plans[base]
        if REFERENCE_BASE in plans and tuple((o, len(b)) for o, b in records) != tuple(
                (o, len(b)) for o, b in plans[REFERENCE_BASE]):
            raise InvalidModule("Native plan layout depends on module load address")
        return records

    reference = plan(REFERENCE_BASE)
    shifted = plan(REFERENCE_BASE + 0x100000)
    low_shifted = plan(REFERENCE_BASE + 0x8010)
    fixups = [[] for _ in reference]
    for index, ((offset, replacement), (_, next_data), (_, low_data)) in enumerate(zip(reference, shifted, low_shifted)):
        for position in range(0, len(replacement), 4):
            first, second, third = (word(block, position) for block in (replacement, next_data, low_data))
            if first == second == third:
                continue
            if second - first == 0x100000 and 0 <= first - REFERENCE_BASE < len(data):
                kind, relative = 2, first - REFERENCE_BASE
            elif (first >> 26 in (2, 3) and second >> 26 == first >> 26
                  and (second & 0x3FFFFFF) - (first & 0x3FFFFFF) == 0x40000):
                kind, relative = 4, ((first & 0x3FFFFFF) << 2) - REFERENCE_BASE
                if not 0 <= relative < len(data):
                    raise InvalidModule("Jump target outside module")
            elif first >> 16 == second >> 16 == third >> 16 and first == second:
                kind, relative = 6, (first - REFERENCE_BASE) & 65535
            elif first >> 26 == 15 and second >> 16 == first >> 16 and second - first == 16:
                kind = 5
                # Usually the LUI is followed by its ADDIU/ORI, so the carry can
                # be worked out directly instead of searched for.
                following = position + 4
                if following < len(replacement):
                    lower = word(replacement, following)
                    lower_shifted = word(low_data, following)
                    opcode = lower >> 26
                    if (opcode in (9, 13) and (lower >> 21) & 31 == (first >> 16) & 31
                            and lower >> 16 == lower_shifted >> 16
                            and (lower_shifted - lower) & 65535 == 0x8010):
                        immediate = lower & 65535
                        if opcode == 9 and immediate & 0x8000:
                            immediate -= 65536
                        relative = ((first & 65535) << 16) + immediate - REFERENCE_BASE
                        if opcode == 13:
                            relative -= 0x8000
                        fixups[index].append(Fixup(position, kind, anchor.name, relative - anchor.value))
                        # Check both sides of the carry.
                        edge = (-(relative + 0x8000)) & 65535
                        plan(REFERENCE_BASE + ((edge - 1) & ~15))
                        plan(REFERENCE_BASE + ((edge + 15) & ~15))
                        continue
                # Otherwise binary search for the first base where the LUI carries.
                left, right = 0, 4096
                while left + 1 < right:
                    middle = (left + right) // 2
                    value = word(plan(REFERENCE_BASE + middle * 16)[index][1], position)
                    if value == first:
                        left = middle
                    elif value == first + 1:
                        right = middle
                    else:
                        raise InvalidModule("Non-affine HI16 operand")
                relative = ((first & 65535) << 16) - REFERENCE_BASE - 0x8000 + 65536 - right * 16
            else:
                raise InvalidModule(f"Unsupported address-dependent operand at {offset + position:#x}")
            fixups[index].append(Fixup(position, kind, anchor.name, relative - anchor.value))
    edits = tuple(ModuleEdit(offset, data[offset:offset + len(replacement)], replacement, tuple(fixups[index]))
                  for index, (offset, replacement) in enumerate(reference))
    compiled = compile_module(data, edits, arena_start=arena_start)
    rebuilt = SNR2Module(compiled)
    for base in (*tuple(plans), *CHECK_BASES):
        expected = plan(base)
        loaded, _ = rebuilt.relocate(base, imports)
        for offset, replacement in expected:
            if loaded[offset:offset + len(replacement)] != replacement:
                raise InvalidModule(f"Compiled plan differs at {offset:#x}, load base {base:#x}")
    return compiled

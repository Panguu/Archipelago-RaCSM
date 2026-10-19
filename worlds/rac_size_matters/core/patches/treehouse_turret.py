"""Record the Treehouse turret pickup, which has no persistent save flag."""

import struct

from . import asm as m
from .asm import Patch, packed
from .plan import Plan, supported_game_id


def prepare(pine, *, code_start, code, checked=False):
    game_id = supported_game_id(pine)
    signature = packed(0x27BDFFB0, 0xFFB20040, 0xFFB00030, 0x0080902D,
                       0xFFB10038, 0xFFBF0048, 0x8E430064, 0x30620020)
    hits = [i for i in range(0, len(code) - len(signature), 4)
            if code[i:i + len(signature)] == signature]
    if len(hits) != 1:
        raise RuntimeError("Expected one Treehouse turret pickup routine")
    offset = hits[0]
    routine = code[offset:offset + 0x1B8]
    if len(routine) != 0x1B8:
        raise RuntimeError("Truncated Treehouse turret pickup routine")
    words = struct.unpack_from("<6I", routine, 0x110)
    if (words[0], words[2], words[3], words[5]) != (0x2404000E, 0x2405FFFF, 0x2404000E, 0x2405FFFF):
        raise RuntimeError("Treehouse turret reward signature changed")
    if any(word >> 26 != 3 for word in (words[1], words[4])):
        raise RuntimeError("Treehouse turret reward calls changed")
    if routine[0x1A8:] != packed(0xDFBF0048, 0x03E00008, 0x27BD0050, 0):
        raise RuntimeError("Treehouse turret pickup boundary changed")
    start = code_start + offset
    journal = start + 0x1B4
    # The first getter's return is discarded. Record the pickup at that point;
    # retain the second getter and the vanilla equip/ammo/notification behavior.
    replacement = packed(
        m.lui(m.V0, (journal + 0x8000) >> 16),
        m.addiu(m.V1, m.ZERO, 2),
        m.sb(m.V1, journal & 0xFFFF, m.V0),
    )
    plan = Plan(pine, [
        Patch(start + 0x110, routine[0x110:0x11C], replacement),
        Patch(journal, bytes(4), bytes([2 if checked else 1, 0, 0, 0])),
    ], expected_game_id=game_id)
    plan.journals = ((journal, 1),)
    return plan

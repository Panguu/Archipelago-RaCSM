"""Keep the clone arena's MovieTeleport alive on return visits to Quodrona."""

import struct

from . import asm as m
from .asm import Patch, branch, jump, packed
from .plan import Plan, supported_game_id


INIT = packed(0x27BDFFE0, 0xFFB10008, 0xFFBF0010, 0x0080882D,
              0xFFB00000, 0x8E300054, 0x92020014, 0x1040000F)


def prepare(pine, *, code_start, code):
    game_id = supported_game_id(pine)
    hits = [offset for offset in range(0, len(code) - len(INIT) + 1, 4)
            if code[offset:offset + len(INIT)] == INIT]
    if len(hits) != 1:
        raise RuntimeError("Quodrona MovieTeleport initialization changed")
    offset = hits[0]
    start = code_start + offset

    def require(relative, expected):
        if code[offset + relative:offset + relative + len(expected)] != expected:
            raise RuntimeError("Quodrona MovieTeleport replay signature changed")

    # Validate both the mission-bit query and the stage/trigger destinations.
    require(0x50, packed(0x24840002, 0x1440003F, 0x0000102D,
                         0x8E040010, 0x1880000D))
    require(0x98, packed(0x8E040004, 0x10800004))
    require(0x120, packed(0x92230045))
    require(0x128, packed(0xA2200046))
    require(0x154, packed(0xDFB00000, 0xDFB10008, 0xDFBF0010,
                          0x03E00008, 0x27BD0020))
    call = struct.unpack_from('<I', code, offset + 0x4C)[0]
    getter = (call & 0x03FFFFFF) << 2
    getter_offset = getter - code_start
    if (call >> 26 != 3 or not 0 <= getter_offset <= len(code) - 32
            or code[getter_offset + 12:getter_offset + 32]
            != packed(0x00A31804, 0x00862021, 0x948208C0, 0x03E00008, 0x00431024)):
        raise RuntimeError("Quodrona mission-bit getter changed")

    site = start + 0x18
    replacement = packed(
        m.lbu(m.A1, 0x45, m.S1),             # Movie 2 enters the arena; 3 ends it.
        m.addiu(m.V0, m.ZERO, 2),
        m.bne(m.A1, m.V0, 4),
        m.NOP,
        m.addiu(m.V0, m.ZERO, 1),
        branch(site + 20, start + 0x98),     # Still resolve the trigger/arena links.
        m.sb(m.V0, 0x15, m.S0),             # Require walking in even if seen before.
        m.lbu(m.V0, 0x14, m.S0),
        m.beq(m.V0, m.ZERO, 8),             # Other movies retain their stage checks.
        m.addiu(m.A0, m.ZERO, 22),          # Quodrona mission word: 2 * 10 + 2.
        jump(getter),
        m.NOP,
        m.bne(m.V0, m.ZERO, (start + 0x154 - (site + 48) - 4) // 4),
        m.daddu(m.V0, m.ZERO, m.ZERO),
        m.NOP, m.NOP, m.NOP,
    )
    return Plan(pine, [Patch(site, code[offset + 0x18:offset + 0x5C], replacement)],
                expected_game_id=game_id)

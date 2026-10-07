"""Read-only Ratchet progression diagnostics; never awards checks or changes XP."""
import struct
from bisect import bisect_right

from .symbols import require


RATCHET_XP_SAVE_OFFSET = 0x198FC


def read_ratchet_nanotech(pine, symbols):
    addresses = (0x206328, 0x206324, 0x206338, 0x1AAE3C)
    before = pine.batch_read_int32(addresses)
    if before[1:] != [0xFFFFFFFF, 3, 5]:
        raise ValueError("Wait until the level has finished loading")
    pointer, table, getter = require(symbols, "pGV", "g_LevelProgressionExperienceData_Ratchet",
                                     "GLOBALVARS_GetPlayerMaxLevel__FP6PLAYER")
    save = pine.read_int32(pointer)
    if save % 4 or not 0x100000 <= save <= 0x2000000 - RATCHET_XP_SAVE_OFFSET - 4:
        raise ValueError("Ratchet save pointer is not initialized")
    # The Ratchet branch indexes these two row counts by min(challenge mode, 1).
    high, low = struct.unpack('<2I', pine.read_bytes(getter + 0x44, 8))
    if (high & 0xFFFF0000 != 0x3C040000 or low & 0xFFFF0000 != 0x24840000
            or pine.read_int32(getter + 0x58) != 0x8C620000):
        raise ValueError("Ratchet cap getter layout changed")
    cap_address = ((high & 65535) << 16) + ((low & 65535) - (65536 if low & 32768 else 0))
    if cap_address % 4 or not 0x100000 <= cap_address <= 0x1FFFFF8:
        raise ValueError("Invalid Ratchet cap table")
    counts = struct.unpack('<2I', pine.read_bytes(cap_address, 8))
    if not all(1 <= count <= 71 for count in counts):
        raise ValueError("Ratchet cap counts are outside the verified table")
    rows = list(struct.iter_unpack('<3I', pine.read_bytes(table, 71 * 12)))
    if (len(rows) != 71 or any(index != i or hp != 20 + i for i, (index, xp, hp) in enumerate(rows))
            or rows[0][1] != 0 or any(a[1] >= b[1] for a, b in zip(rows, rows[1:]))):
        raise ValueError("Ratchet progression table changed")
    xp, ng = pine.read_int32(save + RATCHET_XP_SAVE_OFFSET), pine.read_int32(save + 0xED4)
    if xp > 0x7FFFFFFF or ng > 2:
        raise ValueError("Invalid saved XP or challenge mode")
    count = counts[min(ng, 1)]
    index = min(bisect_right([row[1] for row in rows], xp) - 1, count - 1)
    hud_address = symbols.get('HUD_g_CurrentMaxHealth')
    hud = struct.unpack('<f', pine.read_bytes(hud_address, 4))[0] if hud_address else None
    if pine.batch_read_int32(addresses) != before or pine.read_int32(pointer) != save:
        raise ValueError("Level changed during read; try again after loading")
    return dict(module=before[0], saved_xp=xp, challenge_mode=ng, xp_nanotech=rows[index][2],
                ng_cap=rows[counts[0] - 1][2], ng_plus_cap=rows[counts[1] - 1][2],
                next_xp=rows[index + 1][1] if index + 1 < count else None,
                hud_max=hud)

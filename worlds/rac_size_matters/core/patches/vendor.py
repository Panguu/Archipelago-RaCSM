"""Native base/Titan purchase interception, independent of item ownership.

Grant blocks are replaced with journal writes reusing their now-unreachable
bytes; no unallocated RAM or ISO edits. Ammo and the mod vendor are untouched.
"""
import struct

from . import mips as m
from .asm import Patch, branch, j, jump, packed
from .plan import Plan


def _word(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def _record(address, table, rebuild):
    # The native item id is the selected menu item's +0x14 field.
    return packed(
        m.lw(m.T0, 0x14, m.S1),
        m.lui(m.T1, (table + 0x8000) >> 16),
        m.addu(m.T1, m.T1, m.T0),
        m.addiu(m.T0, m.ZERO, 2),           # checked
        m.sb(m.T0, table & 0xFFFF, m.T1),
        branch(address + 20, rebuild), m.NOP,
    )


def prepare(pine, *, code_start, code, base_locations, titan_locations, checked=(), eligible_titans=()):
    """Prepare against one settled module snapshot; never writes RAM.

    Maps native item ids to AP location names; pass only eligible Titan offers.
    """
    if pine.get_game_id() != "SCUS-97615":
        raise RuntimeError("Vendor patch requires SCUS-97615")
    for mapping, limit in ((base_locations, 25), (titan_locations, 15)):
        if any(type(slot) is not int or not 2 <= slot < limit for slot in mapping):
            raise ValueError("Invalid vendor item id")
    anchor = packed(0x8E230014, 0x24020018)
    matches = [i for i in range(16, len(code) - 8, 4) if code[i:i + 8] == anchor]
    if len(matches) != 1:
        raise RuntimeError("Expected exactly one native vendor purchase block")
    base = code_start + matches[0] - 16
    titan = base - 56

    def read(address, count):
        offset = address - code_start
        if offset < 0 or offset + count > len(code):
            raise RuntimeError("Vendor function outside supplied code snapshot")
        return code[offset:offset + count]

    def require(address, expected):
        if read(address, len(expected)) != expected:
            raise RuntimeError(f"Vendor instruction signature changed at {address:#x}")

    def target(address):
        word = _word(read(address, 4), 0)
        if word >> 26 != 3:
            raise RuntimeError(f"Expected native call at {address:#x}")
        return (word & 0x03FFFFFF) << 2

    require(base, packed(0x8E240014, 0x24050001))
    setter = target(base + 8)
    require(base + 12, packed(0x24070001))
    require(setter, packed(0x27BDFFD0, 0xFFB10008, 0xFFB00000, 0x0080882D))
    rebuild = target(base + 76)
    offer = rebuild + 0x22C
    getter = target(offer)
    require(getter, packed(0x27BDFFF0, 0xFFBF0000))
    require(getter + 12, packed(0, 0x8C420054, 0xDFBF0000, 0x0002102B,
                                 0x03E00008, 0x27BD0010))
    require(titan, packed(0x8E240014, 0x8E45003C, 0x3887000C, 0x24A50001))
    require(titan + 16, packed(jump(setter + 0x138), 0x0007382B))
    require(rebuild, packed(0x27BDFF70))
    # Only IsSellable and its immediately following base-offer gate are
    # redirected. All ammo queries keep using real gameplay ownership.
    sellable = target(offer - 16)
    require(offer - 12, packed(0x0220202D, 0x10400022, 0x0220202D,
                                jump(getter), 0x2405FFFF))
    require(sellable, packed(0x27BDFFF0, 0x2405FFFF, 0xFFB00000, 0xFFBF0008,
                              jump(getter), 0x0080802D))
    require(rebuild + 0x2CC, packed(0x24130003))
    require(rebuild + 0x2F4, packed(0x8E02003C, 0x54530015, 0x26520001))
    target(rebuild + 0x300)
    require(rebuild + 0x304, packed(0, 0x10400010))

    base_table, titan_table = base + 28, base + 60
    checked = set(checked)
    flags = bytearray([2] * 32 + [3] * 16)
    for offset, mapping in ((0, base_locations), (32, titan_locations)):
        for slot, name in mapping.items():
            flags[offset + slot] = (2 if name in checked else
                                    1 if offset == 0 or slot in eligible_titans else 3)
    native_getter = titan + 28
    get_code = packed(
        m.lui(m.V0, (base_table + 0x8000) >> 16),
        m.addu(m.V0, m.V0, m.A0),
        m.lbu(m.V0, base_table & 0xFFFF, m.V0),
        m.jr(m.RA), m.addiu(m.V0, m.V0, -1),   # return flag - 1
        m.NOP, m.NOP,
    )
    # The vanilla starter routine force-grants starting gear that AP owns
    # instead; redirect its entry and reuse the freed bytes for the Titan journal.
    starter_anchor = packed(0x27BDFFF0, 0x24040002, 0xFFBF0000, jump(getter),
                             0x2405FFFF, 0x38420001, 0x2406FFFF, 0x304700FF)
    starters = [i for i in range(0, len(code) - len(starter_anchor), 4)
                if code[i:i + len(starter_anchor)] == starter_anchor]
    if len(starters) != 1:
        raise RuntimeError("Expected exactly one forced starter-grant routine")
    starter = code_start + starters[0]
    require(starter + 32, packed(0x24040002, jump(setter), 0x24050001))
    native_titan_getter = starter + 8
    titan_gate = packed(
        m.lui(m.V0, (titan_table + 0x8000) >> 16),
        m.addu(m.V0, m.V0, m.S2),
        m.lbu(m.V0, titan_table & 0xFFFF, m.V0),
        m.xori(m.V0, m.V0, 1),
        m.jr(m.RA), m.sltiu(m.V0, m.V0, 1),   # return flag == 1
    )
    # The native row array ends at the following vendor-state global; reserve
    # the upper half of its 4096 bytes, beyond all 64 possible rows.
    def address_pair(upper, lower, hi, lo):
        a, b = _word(read(upper, 4), 0), _word(read(lower, 4), 0)
        if a & 0xFFFF0000 != hi or b & 0xFFFF0000 != lo:
            raise RuntimeError("Vendor row-storage signature changed")
        return ((a & 65535) << 16) + struct.unpack("<h", packed(b)[:2])[0]
    rows = address_pair(rebuild + 0xC, rebuild + 0x1C, 0x3C050000, 0x24A50000)
    end = address_pair(base - 0xF4, base - 0xEC, 0x3C020000, 0xAC400000)
    if not 0x100000 <= rows < end <= 0x2000000 or end - rows != 0x1000:
        raise RuntimeError("Native vendor row capacity changed")
    arena = rows + 0x800
    mode = arena + 0x80  # 0 = AP offers; 1 = owned-weapon ammo

    def view_gate(real, blocked, block_ammo):
        return packed(
            m.lui(m.T0, (mode + 0x8000) >> 16), m.lw(m.T0, mode & 65535, m.T0),
            (m.beq if block_ammo else m.bne)(m.T0, m.ZERO, 3), m.NOP,
            m.jr(m.RA), m.addiu(m.V0, m.ZERO, blocked),
            j(real), m.NOP)

    base_view, titan_view, ammo_view, titan_spec = arena, arena + 32, arena + 64, arena + 96
    base_spec = arena + 0xA0
    runtime_getter = target(rebuild + 0x2D8)
    payload = (view_gate(native_getter, 1, True)
               + view_gate(native_titan_getter, 0, True)
               + view_gate(getter, 0, False)
               + packed(m.jr(m.RA), m.lw(m.V0, 0x1C, m.S0))).ljust(0xA0, b"\0")
    payload += packed(m.addiu(m.SP, m.SP, -16), m.sd(m.RA, 0, m.SP),
                      jump(runtime_getter), m.NOP, m.lw(m.V0, 0x10, m.V0),
                      m.ld(m.RA, 0, m.SP), m.jr(m.RA), m.addiu(m.SP, m.SP, 16))
    require(rebuild + 0x80, packed(jump(getter), 0x2405FFFF))
    require(rebuild + 0x368, packed(jump(getter), 0x2405FFFF))
    require(rebuild + 0x2E8 + 4, packed(0x2405FFFF, 0x0040882D, 0x8E02003C))
    target(rebuild + 0x2E8)
    target(rebuild + 0x24C)
    target(rebuild + 0x260)
    replacements = [
        (base, _record(base, base_table, base + 76) + flags),
        (titan, _record(titan, titan_table, base + 76) + get_code),
        (sellable + 16, packed(jump(base_view))),
        (offer, packed(jump(base_view))),
        (starter, packed(m.jr(m.RA), m.addiu(m.V0, m.ZERO, 1)) + titan_gate),
        (rebuild + 0x300, packed(jump(titan_view))),
        (rebuild + 0x80, packed(jump(ammo_view))),
        (rebuild + 0x368, packed(jump(ammo_view))),
        # Native eligibility comes from the journal; no gameplay level fakes.
        (rebuild + 0x2F8, packed(m.NOP, m.NOP)),
        (rebuild + 0x2E8, packed(jump(titan_spec))),
        (rebuild + 0x24C, packed(jump(base_spec))),
        (rebuild + 0x260, packed(jump(base_spec))),
        (arena, payload),
    ]
    # Row storage is BSS and can lie beyond the supplied executable snapshot.
    # Its bounds were verified above; keep instruction reads snapshot-bound.
    plan = Plan(pine, [Patch(a, pine.read_bytes(a, len(b)) if a == arena
                            else read(a, len(b)), bytes(b)) for a, b in replacements])
    plan.tables = {"base": base_table, "titan": titan_table}
    plan.locations = {"base": dict(base_locations), "titan": dict(titan_locations)}
    plan.journals = ((base_table, 48),)
    plan.starter = starter
    plan.view_mode = mode
    plan.mutable_data = ((mode, 4),)
    return plan

"""Separate Titan transactions from gameplay levels at native vendor call sites."""
from ...constants.native_functions import NativeFunctions
from ...constants.weapon_progression import TITAN_LOCATIONS
from ..inventories.weapons import WEAPON_ORDER
from ..symbols import require
from .asm import Patch, jump, packed
from .patch import PatchSet


class TitanOffers(PatchSet):
    def prepare(self, symbols):
        self.patches = []
        p = self.pine
        """NG+ 0: skip both Titan offer rows regardless of the loaded save's tier."""
        buy = require(symbols, NativeFunctions.SCRNVENDOR_PROCESS_PURCHASE)
        call = p.read_int32(buy + 0x338)
        if call >> 26 != 3:
            raise RuntimeError("Native vendor builder call changed")
        builder = (call & 0x3FFFFFF) << 2
        edits = []
        for offset in (0x63C, 0x6D8):
            site = builder + offset
            if p.read_bytes(site, 12) != packed([0x8E02005C, 0x54540013, 0x26520001]):
                raise RuntimeError("Native Titan offer gate changed")
            # The original BNE likely skips the offer unless its weapon is V4.
            # Always take that skip, preserving the weapon-loop increment delay.
            edits.append(Patch(site + 4, packed([0x54540013]), packed([0x10000013])))
        self.patches = edits
        return edits




class TitanVendor(PatchSet):
    def __init__(self, pine):
        super().__init__(pine)
        self.table = None

    def read(self):
        """Read Titan purchase flags; 3=unchecked and 2=checked."""
        if self.table is None:
            raise RuntimeError("Prepare TitanVendor before reading")
        data = self.pine.read_bytes(self.table, 20)
        if len(data) != 20:
            raise RuntimeError("Incomplete Titan flag table read")
        return data

    def prepare(self, symbols, hooks, checked):
        self.patches = []
        self.table = None
        p = self.pine
        buy, set_power, get_def = require(
            symbols, NativeFunctions.SCRNVENDOR_PROCESS_PURCHASE, NativeFunctions.GADGET_SET_POWER_LEVEL, NativeFunctions.GADGET_GET_DEF_AT_LEVEL,
        )
        # Resolve the exact functions from verified existing call sites instead
        # of relying on optional export aliases.
        original = p.read_bytes(buy + 0x164, 0x70)
        assert p.read_int32(buy + 0x168) == 0x8E440010
        assert p.read_int32(buy + 0x178) == 0x8E05005C
        assert p.read_int32(buy + 0x184) == jump(set_power, True)
        assert p.read_int32(buy + 0x188) == 0x24A50001
        assert p.read_int32(buy + 0x160) == 0
        builder_call = p.read_int32(buy + 0x338)
        assert builder_call >> 26 == 3
        builder = (builder_call & 0x3FFFFFF) << 2
        arena = buy + 0x164
        table, reader, recorder = arena + 8, arena + 28, arena + 80
        flags = bytearray(20)
        mapping = {WEAPON_ORDER.index(i): n for i, n in TITAN_LOCATIONS.items()}
        for slot, name in mapping.items():
            flags[slot] = 2 if name in checked else 3
        # s2=weapon, s4=3. Return past the caller's original branch and icon
        # load when unchecked; otherwise jump to its loop increment (+0x50).
        read = packed([0x3C030000 | (table >> 16), 0x34630000 | (table & 65535),
            0x00721821, 0x90620000, 0x10540004, 0,
            0x27FF0048, 0x03E00008, 0,
            0x8E25002C, 0x27FF0008, 0x03E00008, 0])
        record = packed([0x3C030000 | (table >> 16), 0x34630000 | (table & 65535),
            0x00641821, 0x24020002, 0xA0620000, jump(buy + 0x338), 0, 0])
        payload = packed([jump(recorder), 0]) + bytes(flags) + read + record
        assert len(payload) == 0x70
        edits = [Patch(arena, original, payload),
                 Patch(buy + 0x160, packed([0]), packed([0x8E440010]))]
        for offset in (0x63C, 0x6D8):
            site = builder + offset
            assert p.read_bytes(site, 12) == packed([0x8E02005C, 0x54540013, 0x26520001])
            assert p.read_int32(site - 16) == 0x0040802D  # move s0,v0
            assert p.read_int32(site - 8) == 0x0240202D  # move a0,s2
            assert p.read_int32(site - 4) == 0x0040882D  # move s1,v0
            edits += [Patch(site, p.read_bytes(site, 8), packed([jump(reader, True), 0])),
                      Patch(site - 16, p.read_bytes(site - 16, 8),
                            packed([0x24050003, jump(get_def, True)]))]
        self.table = table
        hooks.tables["titan"] = table
        hooks.locations["titan"] = mapping
        self.patches = edits
        return edits




class TitanPrice(PatchSet):
    def prepare(self, symbols, allocate):
        self.patches = []
        p = self.pine
        """The browsing price must use V4 even if AP has granted another tier."""
        browse, current, fixed = require(
            symbols, NativeFunctions.SCRNVENDOR_UPDATE_BROWSE_STATE, NativeFunctions.GADGET_GET_DATA_DEF, NativeFunctions.GADGET_GET_DEF_AT_LEVEL,
        )
        site = browse + 0x178
        original = p.read_bytes(site, 8)
        assert p.read_int32(site) == jump(current, True)
        assert p.read_int32(site + 4) & 0xFFFF0000 == 0x3C100000
        assert p.read_int32(site + 8) == 0x8C430030
        # s0 is still the selected row here; the original LUI delay slot must
        # run only after testing its type. a0 remains the weapon id.
        # Share the original LUI as the branch delay slot. This must fit the
        # 32-byte remainder of a vendor-only module's hook arena.
        code = packed([0x8E03000C, 0x24020004, 0x14620003,
                       p.read_int32(site + 4), jump(fixed), 0x24050003,
                       jump(current), 0])
        address = allocate(code)
        self.patches = [Patch(site, original, packed([jump(address, True), 0]))]
        return self.patches

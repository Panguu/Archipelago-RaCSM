from ...constants import TITAN_LOCATIONS, WEAPON_ORDER, NativeFunctions
from ..symbols import require
from ..batch_io import read_blocks
from .asm import Patch, jump, packed, words
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
        sites = [builder + offset for offset in (0x63C, 0x6D8)]
        for site, gate in zip(sites, read_blocks(p, [(site, 12) for site in sites])):
            if gate != packed([0x8E02005C, 0x54540013, 0x26520001]):
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

    def prepare(self, symbols, hooks, checked, available_locations=None):
        self.patches = []
        self.table = None
        p = self.pine
        buy, set_power, get_def = require(
            symbols, NativeFunctions.SCRNVENDOR_PROCESS_PURCHASE, NativeFunctions.GADGET_SET_POWER_LEVEL, NativeFunctions.GADGET_GET_DEF_AT_LEVEL,
        )
        # Resolve the exact functions from verified existing call sites instead
        # of relying on optional export aliases.
        guard, original, builder = read_blocks(p, [(buy + 0x160, 4), (buy + 0x164, 0x70), (buy + 0x338, 4)])
        code = words(original)
        assert (code[1], code[5], code[8], code[9]) == (0x8E440010, 0x8E05005C, jump(set_power, True), 0x24A50001)
        assert words(guard) == [0]
        builder_call, = words(builder)
        assert builder_call >> 26 == 3
        builder = (builder_call & 0x3FFFFFF) << 2
        arena = buy + 0x164
        table, reader, recorder = arena + 8, arena + 28, arena + 80
        flags = bytearray(20)
        mapping = {WEAPON_ORDER.index(i): n for i, n in TITAN_LOCATIONS.items()
                   if available_locations is None or n in available_locations}
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
        sites = [builder + offset for offset in (0x63C, 0x6D8)]
        for site, block in zip(sites, read_blocks(p, [(site - 16, 28) for site in sites])):
            code = words(block)
            assert code[4:] == [0x8E02005C, 0x54540013, 0x26520001]
            assert code[0] == 0x0040802D  # move s0,v0
            assert code[2] == 0x0240202D  # move a0,s2
            assert code[3] == 0x0040882D  # move s1,v0
            edits += [Patch(site, block[16:24], packed([jump(reader, True), 0])),
                      Patch(site - 16, block[:8], packed([0x24050003, jump(get_def, True)]))]
        self.table = table
        hooks.tables["titan"] = table
        hooks.locations["titan"] = mapping
        # Only the native offer builder calls this reader. The AP catalog
        # replaces those call sites, so it can reclaim the reader afterwards.
        hooks.catalog_only_ranges.append((reader, recorder))
        self.patches = edits
        return edits




class TitanPrice(PatchSet):
    def prepare(self, symbols, allocate):
        self.patches = []
        p = self.pine
        """Browsing prices use the check tier, independent of AP weapon ownership."""
        browse, current, fixed = require(
            symbols, NativeFunctions.SCRNVENDOR_UPDATE_BROWSE_STATE, NativeFunctions.GADGET_GET_DATA_DEF, NativeFunctions.GADGET_GET_DEF_AT_LEVEL,
        )
        site = browse + 0x178
        block = p.read_bytes(site, 12)
        original = block[:8]
        call, load, read = words(block)
        assert call == jump(current, True)
        assert load & 0xFFFF0000 == 0x3C100000
        assert read == 0x8C430030
        # This call is reached only for base (0) and Titan/Proto (4) rows;
        # ammo and mods have separate branches. Price base checks at V1 and
        # upgrades at V4, regardless of the AP item's received weapon tier.
        code = packed([0x8E03000C, 0x24050000, 0x10600002,
                       load, 0x24050003, jump(fixed), 0])
        address = allocate(code)
        self.patches = [Patch(site, original, packed([jump(address, True), 0]))]
        return self.patches

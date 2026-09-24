"""Vendor transaction flags are independent of AP mod ownership."""
from ...constants.native_functions import NativeFunctions
from ...constants.weapon_mods import WEAPON_MODS, enabled_mods
from ...constants.weapons import EQUIPMENT_DISPLAY_TO_INTERNAL
from ..inventories.weapons import WEAPON_ORDER
from ..symbols import require
from .asm import Patch, jump, packed
from .gain_storage import GainStorage
from .patch import PatchSet


class WeaponMods(PatchSet):
    def __init__(self, pine):
        super().__init__(pine)
        self.enabled = False
        self.catalog = ()
        self.received = set()
        self.base = self.mod_list = self.module = None
        self.validated = False
        self.table = None

    def configure(self, data):
        self.enabled = bool(data.get("weapon_mods", False))
        self.catalog = enabled_mods(data.get("operatives", {}), int(data.get("ng_plus", 0)))
        if "weapon_mod_ids" in data:
            self.catalog = tuple(mod for mod in self.catalog if mod.mod_id in data["weapon_mod_ids"])

    def prepare(self, symbols, hooks, module, checked, vendor_enabled):
        self.patches = []
        self.table = None
        self.base = symbols.get("GADGET_g_GadgetList")
        self.mod_list = symbols.get("GADGET_g_ModList")
        self.module, self.validated = module, False
        if not self.enabled or not vendor_enabled:
            return []
        p = self.pine
        buy, install, installed, alternate, browse = require(
            symbols, NativeFunctions.SCRNVENDOR_PROCESS_PURCHASE, NativeFunctions.GADGET_INSTALL_MOD, NativeFunctions.GADGET_IS_MOD_INSTALLED,
            NativeFunctions.SCRNMODVENDOR_PROCESS_PURCHASE, NativeFunctions.SCRNMODVENDOR_UPDATE_BROWSE_STATE,
        )
        if self.base is None or self.mod_list is None:
            raise RuntimeError("Missing native weapon-mod exports")
        if (p.read_bytes(buy + 0x138, 12) != packed([0x8E450014, jump(install, True), 0x8E440010])
                or p.read_bytes(buy + 0x14C, 8) != packed([0x1000007D, 0])
                or p.read_bytes(alternate + 0x7C, 8) != packed([jump(install, True), 0x0220282D])):
            raise RuntimeError("Native mod purchase layout changed")
        guards, ranges = GainStorage(p).prepare(symbols)
        hooks.extra_ranges = ranges
        recorder = ranges[0][0]
        table, reader = buy + 0x11C, buy + 0x13C
        flags = bytearray([2] * 32)
        mapping = {mod.mod_id: mod.location for mod in self.catalog}
        for mod_id, name in mapping.items():
            flags[mod_id] = 2 if name in checked else 1
        record_code = packed([0x3C030000 | (table >> 16), 0x34630000 | (table & 65535),
                              0x00651821, 0x24020002, 0x03E00008, 0xA0620000])
        read_code = packed([0x3C030000 | (table >> 16), 0x34630000 | (table & 65535),
                            0x00651821, 0x90620000, 0x03E00008, 0x2442FFFF])
        payload = packed([jump(recorder, True), 0x8E450014, jump(buy + 0x338), 0]) + flags + read_code
        assert len(payload) == 0x48
        edits = guards + [Patch(recorder, p.read_bytes(recorder, len(record_code)), record_code),
            Patch(buy + 0x10C, p.read_bytes(buy + 0x10C, len(payload)), bytes(payload)),
            Patch(alternate + 0x7C, packed([jump(install, True)]), packed([jump(recorder, True)]))]
        call = p.read_int32(buy + 0x338)
        if call >> 26 != 3:
            raise RuntimeError("Native vendor builder changed")
        builder = (call & 0x3FFFFFF) << 2
        for site in (builder + 0x37C, builder + 0x56C, browse + 0x2C0, browse + 0xC98):
            if p.read_int32(site) != jump(installed, True):
                raise RuntimeError("Native mod offer ownership gate changed")
            edits.append(Patch(site, packed([jump(installed, True)]), packed([jump(reader, True)])))
        self.table = table
        hooks.tables["mods"], hooks.locations["mods"] = table, mapping
        self.patches = edits
        return edits

    def read(self):
        """Read mod purchase flags independently of installed mod ownership."""
        if self.table is None:
            raise RuntimeError("Prepare an enabled mod vendor before reading")
        data = self.pine.read_bytes(self.table, 32)
        if len(data) != 32:
            raise RuntimeError("Incomplete mod flag table read")
        return data

    def sync(self):
        if not self.enabled or self.base is None or self.mod_list is None:
            return
        p = self.pine
        if (p.read_int32(0x206328) != self.module or p.read_int32(0x206324) != 0xFFFFFFFF
                or p.read_int32(0x206338) != 3):
            return
        if not self.validated:
            for mod in WEAPON_MODS:
                base = self.base + WEAPON_ORDER.index(EQUIPMENT_DISPLAY_TO_INTERNAL[mod.weapon]) * 0x74
                definition = p.read_int32(self.mod_list + mod.mod_id * 4)
                if not 0x100000 <= definition < 0x2000000 or p.read_int32(base + 0x30 + mod.slot * 4) != definition:
                    raise RuntimeError(f"Native mod catalog changed: {mod.name}")
            self.validated = True
        writes = []
        active = {mod.name for mod in self.catalog}
        for mod in WEAPON_MODS:
            address = self.base + WEAPON_ORDER.index(EQUIPMENT_DISPLAY_TO_INTERNAL[mod.weapon]) * 0x74 + 0x68 + mod.slot
            desired = int(mod.name in active and mod.name in self.received)
            if p.read_int8(address) != desired:
                writes.append((address, desired))
        if writes:
            p.batch_write_int8(writes)

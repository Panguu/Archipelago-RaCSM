from ...constants import (
    EQUIPMENT_DISPLAY_TO_INTERNAL,
    WEAPON_MODS,
    WEAPON_ORDER,
    NativeFunctions,
    enabled_challenge_mods,
    enabled_mods,
)
from ..symbols import require
from ..batch_io import read_blocks
from .asm import Patch, jump, packed, words
from .gain_storage import GainStorage
from .patch import PatchSet


class WeaponMods(PatchSet):
    def __init__(self, pine):
        super().__init__(pine)
        self.enabled = False
        self.catalog = ()
        self.challenge_mods = ()
        self.received = set()
        self.base = self.mod_list = self.module = None
        self.validated = False
        self.table = None

    def configure(self, data):
        self.enabled = True
        self.catalog = tuple(mod for mod in enabled_mods(data.get("operatives", {}), int(data.get("ng_plus", 0)))
                             if mod.mod_id in data.get("weapon_mod_ids", ()))
        self.challenge_mods = enabled_challenge_mods(data.get("operatives", {}))

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
        install_call, install_skip, alternate_call, call = read_blocks(
            p, [(buy + 0x138, 12), (buy + 0x14C, 8), (alternate + 0x7C, 8), (buy + 0x338, 4)])
        if (install_call != packed([0x8E450014, jump(install, True), 0x8E440010])
                or install_skip != packed([0x1000007D, 0])
                or alternate_call != packed([jump(install, True), 0x0220282D])):
            raise RuntimeError("Native mod purchase layout changed")
        guards, ranges = GainStorage(p).prepare(symbols)
        hooks.extra_ranges = ranges
        hooks.gain_storage_prepared = True
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
        call, = words(call)
        if call >> 26 != 3:
            raise RuntimeError("Native vendor builder changed")
        builder = (call & 0x3FFFFFF) << 2
        sites = (builder + 0x37C, builder + 0x56C, browse + 0x2C0, browse + 0xC98)
        *gates, record_original, payload_original = read_blocks(
            p, [*((site, 4) for site in sites), (recorder, len(record_code)), (buy + 0x10C, len(payload))])
        edits = guards + [Patch(recorder, record_original, record_code),
            Patch(buy + 0x10C, payload_original, bytes(payload)),
            Patch(alternate + 0x7C, packed([jump(install, True)]), packed([jump(recorder, True)]))]
        for site, gate in zip(sites, gates):
            if gate != packed([jump(installed, True)]):
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
        bases = [self.base + WEAPON_ORDER.index(EQUIPMENT_DISPLAY_TO_INTERNAL[mod.weapon]) * 0x74 for mod in WEAPON_MODS]
        catalog = [] if self.validated else [
            address for mod, base in zip(WEAPON_MODS, bases)
            for address in (self.mod_list + mod.mod_id * 4, base + 0x30 + mod.slot * 4)]
        owned = [base + 0x68 + mod.slot for mod, base in zip(WEAPON_MODS, bases)]
        data = read_blocks(p, [*((address, 4) for address in (0x206328, 0x206324, 0x206338, *catalog)),
                               *((address, 1) for address in owned)])
        module, loading, state, *catalog_words = (int.from_bytes(word, "little") for word in data[:3 + len(catalog)])
        if module != self.module or loading != 0xFFFFFFFF or state != 3:
            return
        if not self.validated:
            for mod, definition, slot in zip(WEAPON_MODS, catalog_words[::2], catalog_words[1::2]):
                if not 0x100000 <= definition < 0x2000000 or slot != definition:
                    raise RuntimeError(f"Native mod catalog changed: {mod.name}")
            self.validated = True
        writes = []
        # Challenge rewards install natively on completion; revoking them here
        # leaves every mod, sold or awarded, owned only once AP sends its item.
        active = {mod.name for mod in (*self.catalog, *self.challenge_mods)}
        for mod, address, current in zip(WEAPON_MODS, owned, data[3 + len(catalog):]):
            desired = int(mod.name in active and mod.name in self.received)
            if current[0] != desired:
                writes.append((address, desired))
        if writes:
            p.batch_write_int8(writes)

"""Build the shared shop from AP transaction flags, not the native save roster."""
import struct

from ...constants.challenge_mode import CHALLENGE_VENDOR_LOCATIONS
from ...constants.native_functions import NativeFunctions
from ...constants.vendor_unlocks import VENDOR_CASES
from ...constants.weapon_mods import WEAPON_MODS
from ...constants.weapons import EQUIPMENT_DISPLAY_TO_INTERNAL
from ..inventories.weapons import WEAPON_ORDER
from ..symbols import require
from . import mips as m
from .asm import Patch, branch, jump, packed, words
from .patch import PatchSet
from .vendor_tabs import VendorTabs


class VendorCatalog(PatchSet):
    START = 0x70
    END = 0x738
    ROW_SIZE = 0x1C
    ICON = 73

    @staticmethod
    def entries(hooks):
        mods = {mod.mod_id: WEAPON_ORDER.index(EQUIPMENT_DISPLAY_TO_INTERNAL[mod.weapon])
                for mod in WEAPON_MODS}
        result = []
        for kind, node_type, unchecked in (("vendor", 0, 1), ("mods", 3, 1), ("titan", 4, 3)):
            for slot in hooks.locations.get(kind, {}):
                weapon, mod = (mods[slot], slot) if kind == "mods" else (slot, 0)
                result.append((hooks.tables[kind] + slot,
                               weapon | mod << 8 | node_type << 16 | unchecked << 24))
        return result

    @staticmethod
    def routine(descriptors, count, header_low, add_item, has_items, affordable, address, tail):
        code = [*m.li32(m.S1, descriptors), *m.li32(m.S2, descriptors + count * 8),
                m.addiu(m.S3, m.S7, header_low)]
        if count:
            loop = len(code)
            code += [m.lw(m.T0, 0, m.S1), m.lbu(m.V0, 0, m.T0), m.lw(m.S0, 4, m.S1),
                     m.srl(m.T3, m.S0, 24)]
            skip = len(code)
            code += [0, 0, m.addu(m.A0, m.S3, m.ZERO), m.addiu(m.A1, m.ZERO, VendorCatalog.ICON),
                     m.addu(m.A2, m.ZERO, m.ZERO), m.srl(m.A3, m.S0, 16), m.andi(m.A3, m.A3, 255),
                     m.andi(m.T0, m.S0, 255), m.srl(m.T1, m.S0, 8), m.andi(m.T1, m.T1, 255),
                     jump(add_item, True), m.addu(m.T2, m.ZERO, m.ZERO)]
            code[skip] = m.bne(m.V0, m.T3, len(code) - skip - 1)
            code += [m.addiu(m.S1, m.S1, 8), m.bne(m.S1, m.S2, loop - len(code) - 2), 0]
        # The browse routine still checks the selected item's actual price.
        # Read the number added (not the number of descriptors) for an empty shop.
        code += [m.lw(m.V1, 0x54, m.S3), m.sltu(m.V1, m.ZERO, m.V1)]
        for flag in (has_items, affordable):
            code += [*m.li32(m.T0, flag), m.sb(m.V1, 0, m.T0)]
        code += [branch(address + len(code) * 4, tail), 0]
        return packed(code)

    def sync_cases(self, owned_cases):
        # Change only the descriptor comparison byte. Transaction flags remain
        # untouched, so unlocking a purchased slot cannot resurrect its check.
        owned_cases = frozenset(owned_cases)
        state = (owned_cases, getattr(self, "challenge_level", 1))
        if getattr(self, "_synced_cases", None) == state:
            return
        writes = []
        for address, case, unchecked in self.case_descriptors:
            allowed = case in owned_cases and (state[1] > 0 or
                address not in getattr(self, "challenge_descriptors", set()))
            desired = unchecked if allowed else 255
            if self.pine.read_int8(address) != desired:
                writes.append((address, desired))
        if writes:
            self.pine.batch_write_int8(writes)
        self._synced_cases = state

    def prepare(self, symbols, hooks):
        p = self.pine
        buy, begin, add, end = require(symbols, NativeFunctions.SCRNVENDOR_PROCESS_PURCHASE,
            "ICONMENU_BeginAddingMenuItems__FP9tICONMENUPvUi",
            "ICONMENU_AddItem__FP9tICONMENUUiUiUiUiUiUi",
            "ICONMENU_EndAddingMenuItems__FP9tICONMENU")
        call = p.read_int32(buy + 0x338)
        if call >> 26 != 3:
            raise RuntimeError("Vendor rebuild call changed")
        builder = (call & 0x3FFFFFF) << 2
        original = p.read_bytes(builder, self.END)
        w = words(original)
        guards = {0: 0x27BDFF70, 0x4C: jump(begin, True), 0x54: 0x27A20010,
                  0x70: 0x24020011, 0x300: jump(add, True), 0x43C: jump(add, True),
                  0x4DC: jump(add, True), 0x660: jump(add, True), 0x6FC: jump(add, True)}
        if (any(w[offset // 4] != value for offset, value in guards.items())
                or p.read_int32(builder + 0x740) != jump(end, True)
                or w[0x24 // 4] & 0xFFFF0000 != 0x24840000
                or w[0x58 // 4] & 0xFFFF0000 != 0x3C030000
                or w[0x60 // 4] & 0xFFFF0000 != 0x3C020000
                or w[0x64 // 4] & 0xFFFF0000 != 0xA0600000
                or w[0x68 // 4] & 0xFFFF0000 != 0xA0400000):
            raise RuntimeError("Vendor catalog layout changed")
        def global_address(upper, lower):
            low = w[lower // 4] & 65535
            return ((w[upper // 4] & 65535) << 16) + (low - 65536 if low & 32768 else low)
        entries = self.entries(hooks)
        catalog_start = builder + self.START + 8
        args = (len(entries), w[0x24 // 4] & 65535, add,
                global_address(0x58, 0x64), global_address(0x60, 0x68),
                catalog_start, builder + self.END)
        code = self.routine(0, *args)
        descriptors = catalog_start + len(code)
        code = self.routine(descriptors, *args)
        self._synced_cases = None
        self.case_descriptors = []
        self.challenge_descriptors = set()
        index = 0
        for kind in ("vendor", "mods", "titan"):
            for name in hooks.locations.get(kind, {}).values():
                self.case_descriptors.append((descriptors + index * 8 + 7,
                                              VENDOR_CASES[name], 3 if kind == "titan" else 1))
                if name in CHALLENGE_VENDOR_LOCATIONS:
                    self.challenge_descriptors.add(descriptors + index * 8 + 7)
                index += 1
        buffer = descriptors + len(entries) * 8
        self.tabs = VendorTabs()
        tab_patches, dispatch = self.tabs.prepare(p, symbols, hooks, builder, original, catalog_start,
                                                 descriptors=descriptors, count=len(entries))
        payload = bytearray(original[:self.START]) + dispatch + code
        for entry in entries:
            payload.extend(struct.pack("<2I", *entry))
        # Give ICONMENU its own bounded array in the replaced builder body.
        # This supports the full NG+ catalog without overrunning native storage.
        # The same array serves both tabs. Retail iterates 40 gadget slots and
        # can append a buy-all row, independently of the AP location count.
        payload.extend(bytes(max(41, len(entries)) * self.ROW_SIZE))
        if len(payload) > self.END:
            raise RuntimeError("AP vendor catalog exceeds verified storage")
        struct.pack_into("<I", payload, 0x0C, m.lui(m.A1, (buffer + 0x8000) >> 16))
        struct.pack_into("<I", payload, 0x1C, m.addiu(m.A1, m.A1, buffer & 65535))
        # The old individual offer gates are superseded; purchase recorders
        # and their flag tables remain installed outside this function.
        hooks.patches[:] = [patch for patch in hooks.patches
                           if not builder <= patch.address < builder + self.END]
        for start, end in getattr(hooks, "catalog_only_ranges", ()):
            patch = next(patch for patch in hooks.patches
                         if patch.address <= start and end <= patch.address + len(patch.replacement))
            hooks.patches.remove(patch)
            for low, high in ((patch.address, start), (end, patch.address + len(patch.replacement))):
                if low < high:
                    a, b = low - patch.address, high - patch.address
                    hooks.patches.append(Patch(low, patch.original[a:b], patch.replacement[a:b]))
            hooks.extra_ranges.append((start, end))
        self.patches = tab_patches + [Patch(builder, original[:len(payload)], bytes(payload))]
        # The replacement branches straight to END, bypassing this tail.
        # Reserve the complete row buffer above before sharing any space.
        free_start = builder + ((len(payload) + 3) & ~3)
        if free_start < builder + self.END:
            hooks.extra_ranges.append((free_start, builder + self.END))
        return self.patches

from .compiled_memory import load_plan
import struct
import unittest
from pathlib import Path

from ..constants import PICKUP_LOCATIONS, VENDOR_LOCATIONS, WEAPON_MODS, ProgressiveWeaponsOptions, SACCases as C
from ..core.patches import (
    LocationHooks,
    Progression,
    TitanOffers,
    TitanPrice,
    TitanVendor,
    VendorCatalog,
    WeaponMods,
    jump,
    packed,
)
from ..core import RuntimeSymbols
from .mips_cpu import CPU
from .test_native_capture_plans import CaptureMemory


class VendorCatalogTests(unittest.TestCase):
    def test_roster_uses_checks_and_preserves_transaction_identity(self):
        p = CaptureMemory()
        p.write_int32 = lambda a, v: p.batch_write_int32([(a, v)])
        p.write_int8 = lambda a, v: p.batch_write_int8([(a, v)])
        start, descriptors, header, add, tail = 0x110000, 0x120000, 0x130000, 0x140000, 0x110700
        entries = [(0x160000 + i, weapon | mod << 8 | kind << 16 | unchecked << 24)
                   for i, (weapon, mod, kind, unchecked) in enumerate(
                       ((5, 0, 0, 1), (5, 10, 3, 1), (5, 0, 4, 3)))]
        for i, entry in enumerate(entries):
            p.write_bytes(descriptors + i * 8, struct.pack('<2I', *entry))
        code = VendorCatalog.routine(descriptors, 3, 0, add, 0x170000, 0x170001, start, tail)
        p.write_bytes(start, code)
        def build(flags):
            p.batch_write_int8([(0x160000 + i, flag) for i, flag in enumerate(flags)])
            p.write_int32(header + 0x54, 0)
            rows = []
            cpu = CPU(p)
            cpu.r[23] = header
            def append(c):
                self.assertEqual(c.r[4], header)
                rows.append(tuple(c.r[5:11]))
                p.write_int32(header + 0x54, len(rows))
                for reg in range(2, 16):
                    c.r[reg] = 0xBAD
            cpu.run(start, stop=tail, stubs={add: append})
            self.assertEqual(p.read_int8(0x170000), bool(rows))
            return rows
        self.assertEqual(build((1, 1, 3)), [(73, 0, 0, 5, 0, 0), (73, 0, 3, 5, 10, 0), (73, 0, 4, 5, 0, 0)])
        self.assertEqual(build((2, 1, 3)), [(73, 0, 3, 5, 10, 0), (73, 0, 4, 5, 0, 0)])
        self.assertEqual(build((2, 2, 3)), [(73, 0, 4, 5, 0, 0)])
        self.assertEqual(build((2, 2, 2)), [])
        self.assertEqual(build((4, 4, 4)), [])

    def test_case_unlocks_filter_native_rows_without_changing_purchase_flags(self):
        p = CaptureMemory()
        start, descriptors, header, add, tail = 0x110000, 0x120000, 0x130000, 0x140000, 0x110700
        entries = ((5, 0, 0, 1, C.GALACTIC_BOLT_RESERVE),
                   (7, 19, 3, 1, C.THE_SHOWERS),
                   (5, 0, 4, 3, C.GALACTIC_BOLT_RESERVE))
        p.write_int8 = lambda a, v: p.batch_write_int8([(a, v)])
        catalog = VendorCatalog(p)
        catalog.case_descriptors = []
        for i, (weapon, mod, kind, unchecked, case) in enumerate(entries):
            p.write_bytes(descriptors + i * 8, struct.pack('<2I', 0x160000 + i,
                weapon | mod << 8 | kind << 16 | unchecked << 24))
            p.batch_write_int8([(0x160000 + i, unchecked)])
            catalog.case_descriptors.append((descriptors + i * 8 + 7, case, unchecked))
        p.write_bytes(start, catalog.routine(descriptors, 3, 0, add, 0x170000, 0x170001, start, tail))
        def build(cases):
            catalog.sync_cases(cases)
            rows = []
            cpu = CPU(p)
            cpu.r[23] = header
            cpu.run(start, stop=tail, stubs={add: lambda c: rows.append((c.r[7], c.r[8], c.r[9]))})
            return rows
        self.assertEqual(build(set()), [])
        self.assertEqual(build({C.THE_SHOWERS}), [(3, 7, 19)])
        self.assertEqual(build({C.GALACTIC_BOLT_RESERVE}), [(0, 5, 0), (4, 5, 0)])
        self.assertEqual(p.read_bytes(0x160000, 3), bytes((1, 1, 3)))
        p.batch_write_int8([(0x160000, 2)])
        self.assertEqual(build(set()), [])
        self.assertEqual(build({C.GALACTIC_BOLT_RESERVE}), [(4, 5, 0)])
        self.assertEqual(p.read_int8(0x160000), 2)

    def test_browsing_price_uses_base_or_upgrade_tier(self):
        p = CaptureMemory()
        browse, current, fixed, storage = 0x110000, 0x120000, 0x130000, 0x140000
        p.write_bytes(browse + 0x178, packed([jump(current, True), 0x3C100059, 0x8C430030]))
        def allocate(code):
            p.write_bytes(storage, code)
            return storage
        TitanPrice(p).prepare({'SCRNVENDOR_UpdateBrowseState__Fv': browse,
            'GADGET_GetDataDef__FUi': current, 'GADGET_GetDefAtLevel__FUiUi': fixed}, allocate)
        for kind, tier in ((0, 0), (4, 3)):
            p.batch_write_int32([(0x15000C, kind)])
            cpu = CPU(p)
            cpu.r[16], cpu.r[4] = 0x150000, 5
            cpu.run(storage, stop=fixed)
            self.assertEqual((cpu.r[4], cpu.r[5], cpu.r[16]), (5, tier, 0x590000))

    def test_complete_catalog_fits_captured_vendor_and_restores(self):
        capture = Path(__file__).parents[1] / '.research/vendor_audit_live.ram'
        if not capture.exists():
            capture = capture.with_name('sac_finished.p2s.ram')
        if not capture.exists():
            self.skipTest('Local vendor audit capture unavailable')
        raw = capture.read_bytes()
        symbols = RuntimeSymbols.parse(raw[:0x1000000], 0)
        for ng in (0, 1, 2):
            p = CaptureMemory()
            p.data[:] = raw
            hooks = LocationHooks(p)
            hooks.prepare(symbols, pickup_locations=PICKUP_LOCATIONS, vendor_locations=VENDOR_LOCATIONS, entitlements={})
            mods = WeaponMods(p)
            mods.configure({'operatives': {'Clank': 1, 'Ratchet': 1}, 'ng_plus': ng, 'weapon_mod_ids': [mod.mod_id for mod in WEAPON_MODS]})
            hooks.patches.extend(mods.prepare(symbols, hooks, 3, set(), True))
            hooks.patches.extend(TitanVendor(p).prepare(symbols, hooks, set()) if ng else TitanOffers(p).prepare(symbols))
            progression = Progression(p)
            progression.configure({'ng_plus': ng, 'progressive_weapons': ProgressiveWeaponsOptions.AUTOMATIC})
            hooks.patches.extend(VendorCatalog(p).prepare(symbols, hooks))
            hooks.patches.extend(progression.prepare(symbols, hooks, 3))
            spans = sorted((p.address, p.address + len(p.replacement)) for p in hooks.patches)
            self.assertTrue(all(b <= c for (_, b), (c, _) in zip(spans, spans[1:])))
            load_plan(hooks)
            if ng == 1:
                self.check_purchase_paths(p, symbols, hooks)
            for change in reversed(hooks.patches):
                p.write_bytes(change.address, change.original)
            if ng != 1:
                self.assertEqual(p.data, raw)

    def check_purchase_paths(self, p, symbols, hooks):
        p.write_int32 = lambda a, v: p.batch_write_int32([(a, v)])
        p.write_int8 = lambda a, v: p.batch_write_int8([(a, v)])
        buy = symbols['SCRNVENDOR_ProcessPurchase__Fv']
        builder = (p.read_int32(buy + 0x338) & 0x3FFFFFF) << 2
        def pair(upper, lower):
            low = p.read_int32(lower) & 65535
            return ((p.read_int32(upper) & 65535) << 16) + (low - 65536 if low & 32768 else low)
        header = pair(buy + 8, buy + 24)
        price = pair(buy + 72, buy + 88)
        save = p.read_int32(pair(buy + 0x2C, buy + 0x40))
        buffer = pair(builder + 0x0C, builder + 0x1C)
        add = symbols['ICONMENU_AddItem__FP9tICONMENUUiUiUiUiUiUi']
        rows = []
        def rebuild(_cpu=None):
            rows.clear()
            p.write_bytes(header, struct.pack('<4I', buffer, 0, 3, 0))
            p.write_int32(header + 0x54, 0)
            cpu = CPU(p)
            cpu.r[23] = (p.read_int32(builder + 4) & 65535) << 16
            def append(c):
                row = (1, c.r[5], c.r[6], c.r[7], c.r[8], c.r[9], c.r[10])
                p.write_bytes(buffer + len(rows) * 28, struct.pack('<7I', *row))
                rows.append(row)
                p.write_int32(header + 0x54, len(rows))
            cpu.run(builder + 0x70, stop=builder + 0x738, stubs={add: append}, max_steps=5000)
            p.write_int32(header + 4, len(rows))
        rebuild()
        self.assertEqual(len(rows), len(VendorCatalog.entries(hooks)))
        def selected(c):
            c.r[2] = buffer + p.read_int32(header + 12) * 28
        def row_type(kind):
            return lambda c: c.r.__setitem__(2, int(p.read_int32(c.r[4] + 12) == kind))
        def select(c):
            p.write_int32(header + 12, min(c.r[5], max(0, len(rows) - 1)))
        stubs = {builder: rebuild,
            symbols['ICONMENU_GetCurrentItemNode__FP9tICONMENU']: selected,
            symbols['SCRNVENDOR_IsMaxAmmoItem__FP14tICONMENU_NODE']: row_type(2),
            symbols['SCRNVENDOR_IsAmmo__FP14tICONMENU_NODE']: row_type(1),
            symbols['SCRNVENDOR_IsWeaponMod__FP14tICONMENU_NODE']: row_type(3),
            symbols['SCRNVENDOR_IsTitan__FP14tICONMENU_NODE']: row_type(4),
            symbols['GADGET_GetData__FUi']: lambda c: c.r.__setitem__(2, 0x180000),
            symbols['GADGET_GetDataDef__FUi']: lambda c: c.r.__setitem__(2, 0x180000),
            symbols['ICONMENU_SetCurrentSelectedItem__FP9tICONMENUUi']: select,
            (p.read_int32(buy + 0x344) & 0x3FFFFFF) << 2: lambda c: None}
        for kind, table_kind in ((0, 'vendor'), (3, 'mods'), (4, 'titan')):
            index, row = next((i, row) for i, row in enumerate(rows) if row[3] == kind)
            identity = row[3:6]
            slot = row[5] if kind == 3 else row[4]
            count = len(rows)
            p.write_int32(header + 12, index)
            p.write_int32(price, 1234)
            p.write_int32(save + 0xEC8, 100000)
            CPU(p).run(buy, stubs=stubs)
            self.assertEqual(p.read_int32(save + 0xEC8), 98766)
            self.assertEqual(p.read_int8(hooks.tables[table_kind] + slot), 2)
            self.assertEqual(len(rows), count - 1)
            self.assertFalse(any(row[3:6] == identity for row in rows))

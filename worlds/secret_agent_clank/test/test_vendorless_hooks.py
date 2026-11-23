from .compiled_memory import load_plan
import unittest
from unittest.mock import patch

from ..constants import NativeFunctions as F
from ..core import read_blocks
from ..core.patches import LocationHooks, jump, packed
from .mips_cpu import CPU
from .test_native_capture_plans import CaptureMemory


def fake_storage(storage, original):
    def triangle_storage(pine, symbols, extra=()):
        return (storage, original, *read_blocks(pine, extra))
    return triangle_storage


class VendorlessHooksTests(unittest.TestCase):
    def setUp(self):
        self.p = CaptureMemory()
        self.p.write_int32(0x206328, 28)
        self.base, self.init, self.load, self.restart = 0x120000, 0x130000, 0x140000, 0x150000
        self.symbols = {"GADGET_g_GadgetList": self.base, F.MOBY_INIT_MOBYS: self.init,
                        F.LEVEL_LOAD_LEVEL: self.load, F.LEVEL_RESTART: self.restart}
        for site in (self.load + 0x2F0, self.restart + 0x12C):
            self.p.write_bytes(site, packed([jump(self.init, True), 0]))

    def test_no_pickup_or_vendor_exports_still_initialize_equipment(self):
        storage = 0x160000
        self.p.write_bytes(storage, b"\xAA" * 352)
        hooks = LocationHooks(self.p)
        before = bytes(self.p.data)
        with patch("worlds.secret_agent_clank.core.patches.equipment_only.triangle_storage",
                   side_effect=fake_storage(storage, bytes(self.p.data[storage:storage + 352]))):
            hooks.prepare(self.symbols, pickup_locations={}, vendor_locations={},
                          entitlements={2: True, 3: False}, vendor_enabled=False)
        self.assertEqual(bytes(self.p.data), before)
        self.assertEqual(hooks.tables, {})
        self.assertTrue(all(not (edit.address < storage + 352 and edit.address + len(edit.replacement) > storage + 152)
                            for edit in hooks.patches))
        load_plan(hooks)
        for slot in range(40):
            self.p.write_int32(self.base + slot * 0x74 + 0x70, 7)
        for site in (self.load + 0x2F0, self.restart + 0x12C):
            target = (self.p.read_int32(site) & 0x3FFFFFF) << 2
            cpu = CPU(self.p)
            cpu.r[4:7] = [123, 456, 789]
            cpu.run(target, stop=self.init)
            self.assertEqual(cpu.r[4:7], [123, 456, 789])
            self.assertEqual(cpu.r[31], CPU.STOP)
            self.assertEqual(self.p.read_int32(self.base + 2 * 0x74 + 0x70), 1)
            self.assertEqual(self.p.read_int32(self.base + 3 * 0x74 + 0x70), 0)
            self.assertEqual(self.p.read_int32(self.base + 4 * 0x74 + 0x70), 7)
        self.assertEqual(self.p.read_int8(hooks.entitlement_table + 40), 2)

    def test_mid_level_entitlement_change_updates_live_ownership(self):
        storage = 0x160000
        self.p.write_bytes(storage, b"\xAA" * 352)
        hooks = LocationHooks(self.p)
        with patch("worlds.secret_agent_clank.core.patches.equipment_only.triangle_storage",
                   side_effect=fake_storage(storage, bytes(self.p.data[storage:storage + 352]))):
            hooks.prepare(self.symbols, pickup_locations={}, vendor_locations={},
                          entitlements={2: False, 3: True}, vendor_enabled=False)
        load_plan(hooks)
        for slot in range(40):
            self.p.write_int32(self.base + slot * 0x74 + 0x70, 7)
        hooks.sync_entitlements({2: False, 3: True})
        self.assertEqual(self.p.read_int32(self.base + 2 * 0x74 + 0x70), 7)
        hooks.sync_entitlements({2: True, 3: True})
        self.assertEqual(self.p.read_int32(self.base + 2 * 0x74 + 0x70), 1)
        self.assertEqual(self.p.read_int32(self.base + 3 * 0x74 + 0x70), 7)
        self.assertEqual(self.p.read_int32(self.base + 4 * 0x74 + 0x70), 7)
        self.assertEqual(self.p.read_int8(hooks.entitlement_table + 2), 2)

    def test_pickup_checks_need_no_vendor_exports_or_vendor_tables(self):
        give, wait, wait_pickup, get, put = 0x170000, 0x180000, 0x190000, 0x1A0000, 0x1B0000
        self.symbols.update({F.WEAPON_PICKUP_GIVE_WEAPON: give,
                             F.WEAPON_PICKUP_UPDATE_WAIT: wait,
                             F.WEAPON_PICKUP_UPDATE_WAIT_FOR_PICKUP: wait_pickup,
                             F.GADGET_PLAYER_HAS_GADGET: get, F.GADGET_SET_GADGET_OWNERSHIP_STATUS: put})
        self.p.write_int32(give, 0x27BDFF90)
        self.p.write_bytes(give + 0x50, packed([jump(put, True), 0x2CC60002, 0x8E450000]))
        self.p.write_bytes(give + 0x278, packed([0xDFB00040, 0xDFB10048, 0xDFB20050,
                                              0xDFB30058, 0xDFBF0060, 0x03E00008, 0x27BD0070]))
        self.p.write_bytes(wait + 0x50, packed([jump(get, True), 0x8E640000]))
        self.p.write_bytes(wait_pickup + 0x48, packed([jump(get, True), 0x8E040000]))
        hooks = LocationHooks(self.p)
        hooks.prepare(self.symbols, pickup_locations={2: "Test pickup"}, vendor_locations={},
                      entitlements={2: False}, vendor_enabled=False)
        self.assertEqual(set(hooks.tables), {"pickup"})
        load_plan(hooks)
        target = (self.p.read_int32(give + 0x50) & 0x3FFFFFF) << 2
        cpu = CPU(self.p)
        cpu.r[4:7] = [2, 1, 1]
        cpu.run(target)
        self.assertEqual(cpu.r[4:7], [2, 1, 1])
        self.assertEqual(hooks.poll(), ["Test pickup"])
        self.assertEqual(hooks.poll(), [])
        self.assertEqual(self.p.read_int32(self.base + 2 * 0x74 + 0x70), 0)

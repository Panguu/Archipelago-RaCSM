import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from ..client.vendor import VendorHandlerMixin
from ..core import address_maps
from ..core.menu import MenuInventory, MenuStateValue
from ..core.purchase_checks import PurchaseChecks
from ..core.vendor import ModVendorMenu, VendorInventory, WeaponVendorMenu
from .test_native_patches import CPU, Memory, plans


class TestPDAVendor(unittest.TestCase):
    def setUp(self):
        self.memory = Memory()
        self.plan, _, _ = plans(self.memory)
        self.plan.install()
        self.menu = MenuInventory(self.memory)
        self.menu.set_base(1)
        self.menu.current = MenuStateValue.PDA
        self.planet = SimpleNamespace(
            menu=self.menu,
            weapons=SimpleNamespace(weapons={"lacerator": True, "concussion_gun": False}),
            check_weapons=Mock(return_value={"gadgets": [], "weapons": [], "levels": [], "titans": []}),
            planet_id=1,
        )
        self.vendor = VendorInventory(
            self.memory, self.planet, None, Mock(),
            is_weapon_ap_owned=lambda name: name == "lacerator",
        )
        self.vendor.native_plan = self.plan
        self.vendor.controller = Mock(side_effect=AssertionError("PDA must not read view controls"))
        self.vendor._purchasable_names = Mock(return_value=["concussion_gun", "pda"])

    def test_pda_uses_ammo_only_and_preserves_native_menu_on_refresh(self):
        self.assertEqual(self.menu.get(), MenuStateValue.PDA)
        self.assertTrue(self.menu.is_vendor)
        self.vendor.pda_vendor()
        self.vendor.pda_vendor()
        self.vendor.force_refresh()
        self.assertEqual(self.memory.read_int32(self.plan.view_mode), 1)
        self.assertEqual(self.menu.update, MenuStateValue.PDA)
        self.assertEqual(self.vendor._items, ["lacerator"])
        self.assertEqual(self.memory.read_int32(address_maps.WEAPON_VENDOR_SLOTS), 1)
        self.assertEqual(self.memory.read_int32(address_maps.WEAPON_VENDOR_ITEMS), 2)
        self.vendor.controller.assert_not_called()
        self.vendor._purchasable_names.assert_not_called()

    def test_native_pda_view_blocks_base_and_titan_but_allows_owned_ammo(self):
        self.vendor.pda_vendor()
        journal = self.memory.read_bytes(self.plan.tables["base"], 48)
        for entry, expected in ((self.plan.arena, 1), (self.plan.arena + 32, 0)):
            cpu = CPU(self.memory)
            cpu.r[4] = cpu.r[18] = 2
            cpu.run(entry)
            self.assertEqual(cpu.r[2], expected)
        ammo_gate = self.plan.arena + 64
        getter = (self.memory.read_int32(ammo_gate + 24) & 0x3FFFFFF) << 2
        for owned in (0, 1):
            cpu = CPU(self.memory)
            cpu.r[4] = 2
            cpu.run(ammo_gate, stubs={getter: lambda c: c.r.__setitem__(2, owned)})
            self.assertEqual(cpu.r[2], owned)
            self.assertEqual(cpu.calls, [getter])
        self.assertEqual(self.memory.read_bytes(self.plan.tables["base"], 48), journal)

    def test_pda_lifecycle_and_return_to_regular_vendor(self):
        core = SimpleNamespace(
            planet=self.planet, vendor=self.vendor, _prev_vendor=MenuStateValue.CLOSED,
            weapon_vendor=WeaponVendorMenu(), mod_vendor=ModVendorMenu(),
            quick_select=Mock(), on_vendor_open=Mock(), on_vendor_close=Mock(),
            _planet_settled=lambda: False, _suppress_forced_starter_items=Mock(),
        )
        checks = PurchaseChecks(core)
        checks._check_vendor_purchases()
        self.assertTrue(core.weapon_vendor.active)
        self.assertFalse(core.mod_vendor.active)
        core.quick_select.freeze.assert_called_once()
        self.planet.check_weapons.assert_not_called()
        self.menu.current = MenuStateValue.CLOSED
        checks._check_vendor_purchases()
        self.assertFalse(core.weapon_vendor.active)
        core.quick_select.restore.assert_called_once()
        core.quick_select.unfreeze.assert_called_once()
        self.assertFalse(self.vendor._pda_open)
        self.vendor.controller = Mock(return_value=None)
        self.menu.current = MenuStateValue.WEAPONS_VENDOR
        checks._check_vendor_purchases()
        self.assertTrue(self.vendor.show_purchasable_weapons)
        self.assertEqual(self.memory.read_int32(self.plan.view_mode), 0)
        self.assertEqual(self.menu.update, MenuStateValue.WEAPONS_VENDOR)

    def test_direct_weapon_vendor_to_pda_transition(self):
        self.vendor.controller = Mock(return_value=None)
        self.vendor.weapon_vendor()
        core = SimpleNamespace(
            planet=self.planet, vendor=self.vendor, _prev_vendor=MenuStateValue.WEAPONS_VENDOR,
            weapon_vendor=WeaponVendorMenu(), mod_vendor=ModVendorMenu(),
            quick_select=Mock(), on_vendor_open=Mock(), on_vendor_close=Mock(),
        )
        PurchaseChecks(core)._check_vendor_purchases()
        self.assertFalse(self.vendor.show_purchasable_weapons)
        self.assertEqual(self.menu.update, MenuStateValue.PDA)
        self.assertEqual(self.vendor._items, ["lacerator"])


class TestPDAHints(unittest.IsolatedAsyncioTestCase):
    async def test_opening_pda_does_not_scout_purchase_locations(self):
        context = SimpleNamespace(
            slot=1, pine_connected=True, send_msgs=AsyncMock(),
            _wiring=SimpleNamespace(
                planet=SimpleNamespace(menu=SimpleNamespace(get=lambda: MenuStateValue.PDA)),
                vendor=Mock(), weapon_vendor=SimpleNamespace(active=True),
            ),
        )
        await VendorHandlerMixin._send_vendor_hints(context)
        context.send_msgs.assert_not_called()
        context._wiring.vendor.purchasable_locations.assert_not_called()

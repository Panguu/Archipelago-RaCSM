import struct
import unittest
from unittest.mock import Mock

from ..constants.clank_gadgets import SACClankGadgets, SACGadgetPickupLocations
from ..constants.planets import CASE_ID_TO_CASE
from ..core.address_maps import CURRENT_CASE_ADDRESS, FORCE_CASE_ADDRESS
from ..core.core import Core
from ..core.inventories.missions import MissionInventory
from ..core.inventories.planets import CaseInventory
from ..core.inventories.weapons import WeaponInventory
from ..core.symbols import RuntimeSymbols
from ..core.vendor import VendorState


class Memory:
    def __init__(self):
        self.data = bytearray(0x800000)
        self.writes = []

    def read_bytes(self, address, size):
        return bytes(self.data[address:address + size])

    def read_int32(self, address):
        return struct.unpack_from("<I", self.data, address)[0]

    def read_int8(self, address):
        return self.data[address]

    def batch_read_int32(self, addresses):
        return [self.read_int32(a) for a in addresses]

    def batch_read_int8(self, addresses):
        return [self.read_int8(a) for a in addresses]

    def batch_write_int32(self, writes):
        for address, value in writes:
            self.writes.append((address, value))
            struct.pack_into("<I", self.data, address, value)

    def batch_write_int8(self, writes):
        for address, value in writes:
            self.writes.append((address, value))
            self.data[address] = value


class RuntimeTests(unittest.TestCase):
    def test_blackout_pen_is_one_item_and_one_location(self):
        from ..items import ALL_ITEMS
        from ..locations import ALL_LOCATIONS
        self.assertIn(SACClankGadgets.BLACK_OUT_PEN, ALL_ITEMS)
        self.assertNotIn("fountainpen", ALL_ITEMS)
        self.assertIn(SACGadgetPickupLocations.BOLTAIRE_MUSEUM_BLACK_OUT_PEN, ALL_LOCATIONS)
        self.assertNotIn("fountainpen", ALL_LOCATIONS)

    def test_blackout_pen_receipt_writes_shared_slot_without_a_check(self):
        memory = Memory()
        core = Core(memory)
        core.case.ratchet_items.set_base(0x100000)
        core.apply_inventory(ratchet={}, clank={SACClankGadgets.BLACK_OUT_PEN: True})
        core._reapply_all_inventories()
        self.assertEqual(memory.read_int32(0x100000 + 17 * 0x74 + 0x70), 1)
        self.assertEqual(core.case.ratchet_items.check(), [])

    def test_all_equipment_names_write_matching_native_slots(self):
        from ..constants.weapons import CLANK_PICKUP_TO_INTERNAL, EQUIPMENT_DISPLAY_TO_INTERNAL
        from ..core.inventories.weapons import WEAPON_ORDER
        from ..items import GADGET_ITEM_TABLE, WEAPON_ITEM_TABLE
        self.assertEqual(set(EQUIPMENT_DISPLAY_TO_INTERNAL), set(WEAPON_ITEM_TABLE))
        self.assertEqual(set(CLANK_PICKUP_TO_INTERNAL), set(GADGET_ITEM_TABLE))
        for display, internal in {**EQUIPMENT_DISPLAY_TO_INTERNAL, **CLANK_PICKUP_TO_INTERNAL}.items():
            with self.subTest(item=display):
                core = Core(Memory())
                core.case.ratchet_items.set_base(0x100000)
                core.apply_inventory(
                    ratchet={name: display == item for item, name in EQUIPMENT_DISPLAY_TO_INTERNAL.items()},
                    clank={item: display == item for item in GADGET_ITEM_TABLE})
                core._reapply_all_inventories()
                slot = WEAPON_ORDER.index(internal)
                self.assertTrue(core._entitlements()[slot])
                self.assertEqual(core.pine.read_int32(0x100000 + slot * 0x74 + 0x70), 1)
                self.assertEqual(core.case.ratchet_items.check(), [])
                core.apply_inventory(ratchet=dict.fromkeys(EQUIPMENT_DISPLAY_TO_INTERNAL.values(), False),
                                     clank=dict.fromkeys(GADGET_ITEM_TABLE, False))
                core._reapply_all_inventories()
                self.assertFalse(core._entitlements()[slot])
                self.assertEqual(core.pine.read_int32(0x100000 + slot * 0x74 + 0x70), 0)

    def test_legacy_pickup_names_use_same_hook_and_write_ownership(self):
        core = Core(Memory())
        core.case.ratchet_items.set_base(0x100000)
        core.apply_inventory(ratchet={"fountainpen": True, "sunglasses": True}, clank={})
        core._reapply_all_inventories()
        for slot in (17, 25):
            self.assertTrue(core._entitlements()[slot])
            self.assertEqual(core.pine.read_int32(0x100000 + slot * 0x74 + 0x70), 1)

    def test_symbol_uses_following_value_not_previous_export(self):
        data = bytearray(512)
        data[128:134] = b"target"
        struct.pack_into("<IIII", data, 0, 0x555555, 0x1021234, 0x600080, 0x123456)
        self.assertEqual(RuntimeSymbols.parse(data, 0x600000), {"target": 0x123456})

    def test_conflicting_symbols_are_rejected(self):
        data = bytearray(512)
        data[128:134] = b"target"
        struct.pack_into("<III", data, 0, 0x1021234, 0x600080, 0x123456)
        struct.pack_into("<III", data, 12, 0x1031234, 0x600080, 0x123460)
        self.assertEqual(RuntimeSymbols.parse(data, 0x600000), {})

    def test_only_vendor_screens_are_active(self):
        memory = Memory()
        vendor = VendorState(memory)
        vendor.set_addr(100)
        for screen in (0, 1, 7, 8, 9, 16, 17, 0x10008):
            struct.pack_into("<I", memory.data, 100, screen)
            self.assertEqual(vendor.active, screen in (8, 16))

    def test_ap_grant_never_reports_a_pickup(self):
        memory = Memory()
        weapons = WeaponInventory(memory)
        weapons.set_base(0x100000)
        weapons.sync()
        weapons.apply_all({"fountainpen": True})
        self.assertEqual(weapons.check(), [])
        self.assertEqual(memory.writes, [(0x100000 + 17 * 0x74 + 0x70, 1)])

    def test_native_pickup_is_observed_then_retracted(self):
        memory = Memory()
        weapons = WeaponInventory(memory)
        weapons.set_base(0x100000)
        weapons.apply_all({"fountainpen": False})
        address = 0x100000 + 17 * 0x74 + 0x70
        struct.pack_into("<I", memory.data, address, 1)
        self.assertEqual(weapons.check(), ["fountainpen"])
        weapons.apply_all({"fountainpen": False})
        self.assertEqual(memory.read_int32(address), 0)

    def test_transition_unbinds_without_writing_old_overlay(self):
        memory = Memory()
        case = CaseInventory(memory)
        case.is_ready = True
        case._prev_case_id = 1
        case.ratchet_items.set_base(0x100000)
        case.on_transition_start = Mock()
        struct.pack_into("<I", memory.data, CURRENT_CASE_ADDRESS, 2)
        struct.pack_into("<I", memory.data, FORCE_CASE_ADDRESS, 0xFFFFFFFF)
        self.assertFalse(case.check_transition())
        self.assertFalse(case.is_ready)
        self.assertFalse(case.ratchet_items.weapons)
        self.assertEqual(memory.writes, [])
        case.on_transition_start.assert_called_once()

    def test_inventory_packet_only_updates_snapshot(self):
        memory = Memory()
        core = Core(memory)
        core.case.is_ready = True
        core.send_location = Mock()
        core.apply_inventory(ratchet={"blaster": True}, clank={})
        self.assertEqual(memory.writes, [])
        core.send_location.assert_not_called()

    def test_mission_unlock_does_not_complete_it(self):
        memory = Memory()
        missions = MissionInventory(memory)
        missions._resolved_cases = {CASE_ID_TO_CASE[1].name: [0x100000, 0x100060, 0x1000C0]}
        memory.data[0x100000] = 1
        self.assertEqual(missions.enforce_owned_first_missions({CASE_ID_TO_CASE[1].name}), 1)
        self.assertEqual(memory.data[0x100000], 2)
        self.assertEqual(missions.check(CASE_ID_TO_CASE[1]), [])

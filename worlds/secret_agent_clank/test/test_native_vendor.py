import struct
import unittest

from .test_runtime import Memory
from ..core.vendor import VendorState, VendorItem, VendorSnapshot, purchased_base_item


class NativeVendorTests(unittest.TestCase):
    def setUp(self):
        self.memory = Memory()
        self.vendor = VendorState(self.memory)
        self.symbols = {'g_PauseModeData': 0x654A00,
                        'SCRNVENDOR_ProcessPurchase__Fv': 0x3CFF10}
        # Signature words observed in the case-10 purchase routine.
        for offset, word in ((8, 0x3C10006D), (24, 0x261043F8),
                             (72, 0x3C070059), (88, 0x8CE303D0),
                             (76, 0x3C080059), (104, 0xA10503D9)):
            struct.pack_into('<I', self.memory.data, 0x3CFF10 + offset, word)
        struct.pack_into('<I', self.memory.data, 0x654A0C, 8)
        struct.pack_into('<4I', self.memory.data, 0x6D43F8, 0x5904F0, 1, 3, 0)
        struct.pack_into('<7I', self.memory.data, 0x5904F0, 1, 20, 0, 0, 26, 0, 0)

    def test_resolves_header_and_reads_selected_pda(self):
        self.assertTrue(self.vendor.bind_runtime(self.symbols))
        self.assertEqual(self.vendor.header_addr, 0x6D43F8)
        self.assertEqual(self.vendor.price_addr, 0x5903D0)
        self.assertEqual(self.vendor.purchase_flag_addr, 0x5903D9)
        self.assertEqual(self.vendor.selected_item().weapon_name, 'clankpda')
        self.assertEqual(self.vendor.selected_item().node_type, 0)
        self.assertEqual(self.memory.writes, [])

    def test_bad_instruction_signature_leaves_rows_unbound(self):
        struct.pack_into('<I', self.memory.data, 0x3CFF10 + 104, 0)
        self.assertFalse(self.vendor.bind_runtime(self.symbols))
        self.assertEqual(self.vendor.read_items(), [])

    def test_ignores_stale_rows_when_closed(self):
        self.vendor.bind_runtime(self.symbols)
        self.assertEqual(len(self.vendor.read_items()), 1)
        struct.pack_into('<I', self.memory.data, 0x654A0C, 0)
        self.assertEqual(self.vendor.read_items(), [])
        self.vendor.write_item(0, 3)
        self.assertEqual(self.memory.writes, [])

    def test_rejects_invalid_count_and_selection(self):
        self.vendor.bind_runtime(self.symbols)
        for count, selection in ((33, 0), (1, 1), (0, 0)):
            struct.pack_into('<4I', self.memory.data, 0x6D43F8, 0x5904F0, count, 3, selection)
            self.assertEqual(self.vendor.read_items(), [])

    def test_does_not_append_past_native_count(self):
        self.vendor.bind_runtime(self.symbols)
        with self.assertRaises(ValueError):
            self.vendor.write_item(1, 3)
        self.assertEqual(self.memory.writes, [])

    def test_sign_extended_global_addresses(self):
        struct.pack_into('<I', self.memory.data, 0x3CFF10 + 8, 0x3C10006E)
        struct.pack_into('<I', self.memory.data, 0x3CFF10 + 24, 0x2610C3F8)
        self.assertTrue(self.vendor.bind_runtime(self.symbols))
        self.assertEqual(self.vendor.header_addr, 0x6DC3F8)

    def test_purchase_of_last_row_is_reported_once_without_inventory_reads(self):
        self.vendor.bind_runtime(self.symbols)
        struct.pack_into('<I', self.memory.data, 0x5903D0, 35000)
        struct.pack_into('<I', self.memory.data, 0x2075C8, 35491)
        self.assertEqual(self.vendor.poll_purchases(), [])
        struct.pack_into('<I', self.memory.data, 0x2075C8, 491)
        self.memory.data[0x5903D9] = 1
        struct.pack_into('<4I', self.memory.data, 0x6D43F8, 0, 0, 3, 0)
        self.assertEqual(self.vendor.poll_purchases(), ['clankpda'])
        self.assertEqual(self.vendor.poll_purchases(), [])
        self.assertEqual(self.memory.writes, [])


class VendorTransactionTests(unittest.TestCase):
    def setUp(self):
        self.pda = VendorItem(3, 0, 20, 26, 'clankpda', 0)
        self.mod = VendorItem(0, 3, 50, 3, 'shardgun', 4)
        self.before = VendorSnapshot((self.mod, self.pda), 3, 35000, 35491, 0)
        self.after = VendorSnapshot((self.mod,), 0, 10000, 491, 1)

    def test_captured_pda_transaction(self):
        self.assertEqual(purchased_base_item(self.before, self.after), 'clankpda')

    def test_inventory_grant_and_offer_removal_without_payment_are_not_purchase(self):
        self.assertIsNone(purchased_base_item(self.before, self.after._replace(bolts=35491)))

    def test_mod_purchase_does_not_complete_a_weapon_location(self):
        before = self.before._replace(selected_index=0, price=10000)
        after = self.after._replace(rows=(self.pda,), bolts=25491)
        self.assertIsNone(purchased_base_item(before, after))

    def test_unchanged_offer_or_absent_purchase_flag_is_not_purchase(self):
        self.assertIsNone(purchased_base_item(self.before, self.after._replace(rows=self.before.rows)))
        self.assertIsNone(purchased_base_item(self.before, self.after._replace(purchase_flag=0)))

    def test_incorrect_price_or_ambiguous_currency_drop_is_not_purchase(self):
        self.assertIsNone(purchased_base_item(self.before._replace(price=0), self.after))
        self.assertIsNone(purchased_base_item(self.before, self.after._replace(bolts=490)))

    def test_latched_flag_from_prior_purchase_does_not_hide_next_purchase(self):
        self.assertEqual(purchased_base_item(self.before._replace(purchase_flag=1), self.after), 'clankpda')

import unittest
from unittest.mock import Mock
from ..core.titanium_bolts import TitaniumBoltState
from ..constants.titanium_bolts import TITANIUM_BOLT_ENTRIES
from ..locations import TITANIUM_BOLT_LOCATIONS, ALL_LOCATIONS, ALWAYS_ON_LOCATIONS
from .test_runtime import Memory


class TitaniumBoltTests(unittest.TestCase):
    def setUp(self):
        self.reader = TitaniumBoltState(Memory())
        self.reader.valid = True
        self.data = bytearray(15)
        self.reader.flags.read = Mock(side_effect=lambda index, count=1:
                                      bytes(self.data) if index == 0x28 else bytes([0]))

    def test_each_native_id_reports_only_its_own_location(self):
        for (module, index), entry in TITANIUM_BOLT_ENTRIES.items():
            self.data[:] = bytes(15)
            self.data[(module - 1) // 2] = 1 << (((module - 1) & 1) * 4 + index - 1)
            found = self.reader.check()
            self.assertEqual(found, [str(entry)])
            self.reader.confirm(found[0])
            self.assertEqual(self.reader.check(), [])

    def test_unconfirmed_checks_are_retried_on_the_next_check(self):
        first = str(TITANIUM_BOLT_ENTRIES[1, 1])
        self.data[0] = 1
        self.assertEqual(self.reader.check(), [first])
        # Not confirmed -- e.g. the AP client rejected it -- so it must
        # come back on the next check() instead of being dropped forever.
        self.assertEqual(self.reader.check(), [first])
        self.reader.confirm(first)
        self.assertEqual(self.reader.check(), [])

    def test_spending_and_save_rollback_do_not_repeat_checks(self):
        self.data[0] = 3
        found = self.reader.check()
        self.assertEqual(len(found), 2)
        for name in found:
            self.reader.confirm(name)
        self.assertEqual(self.reader.total, 0)
        self.data[0] = 0
        self.assertEqual(self.reader.check(), [])
        self.data[0] = 3
        self.assertEqual(self.reader.check(), [])

    def test_reconnect_deduplicates_server_checks_without_baselining_new_ones(self):
        first = str(TITANIUM_BOLT_ENTRIES[1, 1])
        second = str(TITANIUM_BOLT_ENTRIES[1, 2])
        self.reader.sync_from_ap({first})
        self.data[0] = 3
        self.reader.sync()
        self.assertEqual(self.reader.check(), [second])

    def test_unbound_and_invalid_save_read_do_not_report(self):
        self.reader.valid = False
        self.assertEqual(self.reader.check(), [])
        self.reader.flags.read.assert_not_called()
        self.reader.valid = True
        self.reader.flags.read = Mock(return_value=None)
        self.assertEqual(self.reader.check(), [])

    def test_all_bolts_are_always_on_with_unique_location_ids(self):
        self.assertEqual(len(TITANIUM_BOLT_LOCATIONS), 23)
        self.assertEqual(len(ALL_LOCATIONS), len({v.code for v in ALL_LOCATIONS.values()}))
        for name, data in TITANIUM_BOLT_LOCATIONS.items():
            self.assertEqual(ALWAYS_ON_LOCATIONS[name], data)

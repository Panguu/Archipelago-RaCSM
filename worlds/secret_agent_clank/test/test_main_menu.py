import unittest
from unittest.mock import Mock

from .test_runtime import Memory
from ..core.core import Core
from ..core.main_menu import MainMenuNotice, is_main_menu


class MainMenuTests(unittest.TestCase):
    def setUp(self):
        self.p = Memory()
        self.p.batch_write_int32([(0x1AAE78, 0), (0x1AAE3C, 5), (0x19EF04, 1),
                                 (0x206324, 0xFFFFFFFF), (0x206338, 3), (0x206328, 4)])

    def test_stale_level_id_does_not_hide_title_screen(self):
        self.assertTrue(is_main_menu(self.p))
        self.p.batch_write_int32([(0x1AAE78, 4)])
        self.assertFalse(is_main_menu(self.p))

    def test_loading_boot_and_new_game_request_are_not_menu(self):
        for address, value in ((0x1AAE3C, 4), (0x19EF04, 0), (0x206324, 1), (0x206338, 0)):
            original = self.p.read_int32(address)
            self.p.batch_write_int32([(address, value)])
            self.assertFalse(is_main_menu(self.p))
            self.p.batch_write_int32([(address, original)])

    def test_transition_between_reads_is_rejected(self):
        self.p.batch_read_int32 = Mock(side_effect=[
            [0, 5, 1, 0xFFFFFFFF, 3], [1, 4, 1, 0xFFFFFFFF, 3]])
        self.assertFalse(is_main_menu(self.p))

    def test_message_once_per_visit(self):
        log = Mock()
        notice = MainMenuNotice(self.p, log)
        for _ in range(5):
            notice.poll()
        log.assert_called_once_with('[SAC] Start a new game')
        self.p.batch_write_int32([(0x1AAE78, 1)])
        notice.poll()
        self.p.batch_write_int32([(0x1AAE78, 0)])
        notice.poll()
        self.assertEqual(log.call_count, 2)

    def test_core_shows_notice_without_ap_and_skips_gameplay_reads(self):
        log = Mock()
        core = Core(self.p, log)
        core._read_native_locations = Mock()
        core.case.check_transition = Mock()
        core.tick()
        log.assert_called_once_with('[SAC] Start a new game')
        core._read_native_locations.assert_not_called()
        core.case.check_transition.assert_not_called()

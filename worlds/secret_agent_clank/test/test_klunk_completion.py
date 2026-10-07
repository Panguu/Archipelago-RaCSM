import unittest
from pathlib import Path

from ..constants.missions import CHAPTER_ENTRIES, MISSION_COMPLETE_NAME
from ..constants.planets import SACCases
from ..core.inventories.missions import MissionInventory
from .test_runtime import Memory


class KlunkCompletionTests(unittest.TestCase):
    def test_ending_survives_missing_task_table_and_retries_until_confirmed(self):
        for all_missions in (False, True):
            with self.subTest(all_missions=all_missions):
                p = Memory()
                inv = MissionInventory(p)
                inv.table_base = 0x100000
                mission = CHAPTER_ENTRIES[SACCases.KLUNKS_LAIR][0].name
                expected = mission if all_missions else MISSION_COMPLETE_NAME[SACCases.KLUNKS_LAIR]
                # Entry and mid-fight movies must not count as victory.
                p.data[0x206BF2] = 0x06
                self.assertEqual(inv.check_all(all_missions=all_missions), [])
                p.data[0x206BF2] = 0x0E
                for _ in range(2):
                    self.assertEqual(inv.check_all(all_missions=all_missions), [expected])
                self.assertTrue(inv.completed[mission])
                inv.confirm(expected)
                self.assertEqual(inv.check_all(all_missions=all_missions), [])

    def test_finished_capture_reports_klunk_from_saved_ending(self):
        capture = Path(__file__).parents[1] / '.research/sac_finished.p2s.ram'
        if not capture.exists():
            self.skipTest('Local finished-game capture not present')
        p = Memory()
        p.data[:] = capture.read_bytes()
        inv = MissionInventory(p)
        mission = CHAPTER_ENTRIES[SACCases.KLUNKS_LAIR][0].name
        self.assertIn(mission, inv.check_all(all_missions=True))

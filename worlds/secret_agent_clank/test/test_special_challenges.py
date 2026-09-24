import unittest

from ..constants.special_challenges import SPECIAL_CHALLENGES
from ..core.inventories.special_challenges import SpecialChallengeInventory
from .test_runtime import Memory


class SpecialChallengeTests(unittest.TestCase):
    def test_saved_canals_completions_survive_sync_and_retry(self):
        memory = Memory()
        tracker = SpecialChallengeInventory(memory)
        canals = SPECIAL_CHALLENGES[:3]
        for entry in canals:
            memory.data[entry.event_address] = 1
        expected = [str(entry) for entry in canals]
        tracker.sync()
        self.assertEqual(tracker.check(), expected)
        tracker.sync()
        self.assertEqual(tracker.check(), expected)
        tracker.confirm(expected[0])
        self.assertEqual(tracker.check(), expected[1:])
        tracker.sync_from_ap(set(expected))
        self.assertEqual(tracker.check(), [])

    def test_confirmed_checks_stay_confirmed_across_save_changes(self):
        memory = Memory()
        tracker = SpecialChallengeInventory(memory)
        entry = SPECIAL_CHALLENGES[0]
        tracker.confirm(str(entry))
        tracker.check()
        memory.data[entry.event_address] = 1
        tracker.sync()
        self.assertEqual(tracker.check(), [])

import unittest

from ..constants import (
    CASE_NAME_TO_CASE,
    CHAPTER_ENTRIES,
    CUTSCENE_FLAGS,
    MISSION_COMPLETE_NAME,
    MissionFlag,
    SACCases,
    SACCutsceneLocations,
    SACMissionLocations,
)
from ..core.inventories import MissionInventory
from .test_runtime import Memory

CASE = SACCases.VENANTONIO_LABS
ADDRESSES = [0x100000, 0x100060]


class VenantonioLabsCompletionTests(unittest.TestCase):
    def inventory(self):
        p = Memory()
        inv = MissionInventory(p)
        inv._resolved_cases = {CASE: ADDRESSES}
        inv._story_addresses = {CASE: ADDRESSES}
        inv._resolved_title_ids = {CASE: [entry.title_id for entry in CHAPTER_ENTRIES[CASE]]}
        p.batch_write_int32([(address, MissionFlag.UNLOCKED_COMPLETED) for address in ADDRESSES])
        return p, inv

    def test_frying_pan_waits_for_the_complete_cutscene(self):
        p, inv = self.inventory()
        case = CASE_NAME_TO_CASE[CASE]
        self.assertEqual(inv.check(case), [SACMissionLocations.VENANTONIO_LABS_CRASHING_THE_PARTY])
        flag = CUTSCENE_FLAGS[SACCutsceneLocations.VENANTONIO_LABS_COMPLETE_CUTSCENE]
        p.data[flag.address] |= flag.mask
        self.assertEqual(inv.check(case), [SACMissionLocations.VENANTONIO_LABS_CRASHING_THE_PARTY,
                                           SACMissionLocations.VENANTONIO_LABS_OUT_OF_THE_FRYING_PAN])

    def test_case_complete_waits_for_the_complete_cutscene(self):
        p, inv = self.inventory()
        case = CASE_NAME_TO_CASE[CASE]
        self.assertEqual(inv.check(case, all_missions=False), [])
        flag = CUTSCENE_FLAGS[SACCutsceneLocations.VENANTONIO_LABS_COMPLETE_CUTSCENE]
        p.data[flag.address] |= flag.mask
        self.assertEqual(inv.check(case, all_missions=False), [MISSION_COMPLETE_NAME[CASE]])

"""Audit retail mission predicates against every AP intro cutscene."""
import struct
import unittest
from pathlib import Path

from ..constants.cutscenes import CUTSCENE_FLAGS, SACCutsceneLocations
from ..constants.missions import CHAPTER_ENTRIES, NATIVE_FINISH_CASES
from ..constants.planets import SACCases
from ..core.inventories.cutscenes import CutsceneInventory
from ..core.inventories.missions import MissionInventory, resolve_chapter_table
from ..core.symbols import RuntimeSymbols
from ..locations import ALL_LOCATIONS
from .test_runtime import Memory


class MissionCutsceneIsolationTests(unittest.TestCase):
    def test_each_intro_reports_only_its_own_cutscene(self):
        for name, flag in CUTSCENE_FLAGS.items():
            if not name.endswith(': Enter Cutscene'):
                continue
            with self.subTest(intro=name):
                p = Memory()
                p.data[flag.address] = flag.mask
                self.assertEqual(CutsceneInventory(p).check(), [name])

    def test_casino_completion_bit_still_reports_completion(self):
        p = Memory()
        p.data[0x206BE8] = 2
        self.assertEqual(CutsceneInventory(p).check(), [
            SACCutsceneLocations.HIGH_ROLLERS_CASINO_COMPLETE_CUTSCENE])

    def test_retail_intro_predicates_cannot_report_another_case(self):
        capture = Path(__file__).parents[1] / '.research/SAC.p2s.ram'
        if not capture.exists():
            self.skipTest('Local retail mission table unavailable')
        p = Memory()
        p.data[:] = capture.read_bytes()
        symbols = RuntimeSymbols.parse(p.data[:0x1000000], 0)
        table = symbols['g_MISSION_LEVEL_LIST']
        known = {entry.title_id: case for case, entries in CHAPTER_ENTRIES.items()
                 for entry in entries}
        rows = []
        for pointer, count in resolve_chapter_table(p, table).values():
            for index in range(count):
                address = pointer + index * 0x60
                row = struct.unpack('<24I', p.read_bytes(address, 0x60))
                if row[0] in (1, 4) and row[1] in known:
                    rows.append((address, row))
        self.assertEqual(len(rows), len(known))
        cross_case = set()
        for intro, flag in CUTSCENE_FLAGS.items():
            if not intro.endswith(': Enter Cutscene'):
                continue
            case_name = ALL_LOCATIONS[intro].case
            for all_missions in (False, True):
                with self.subTest(intro=intro, all_missions=all_missions):
                    p.data[0x206BE0:0x206BF6] = bytes(0x16)
                    p.data[flag.address] = flag.mask
                    for address, row in rows:
                        kind, arg, bit = row[8:11]
                        # Retail condition 1 reads a planet's movie bit;
                        # condition 6 reads an individual global flag bit.
                        if kind == 1:
                            byte = 0x206BE0 + ((arg - 1) // 3) * 2 + bit // 8
                            mask = 1 << (bit % 8)
                        elif kind == 6:
                            byte, mask = 0x206BE0 + arg, 1 << bit
                        else:
                            byte, mask = None, 0
                        completed = byte == flag.address and bool(mask & flag.mask)
                        p.write_int32(address + 12, 3 if completed else 2)
                        if completed and known[row[1]] != case_name:
                            cross_case.add(known[row[1]])
                    inv = MissionInventory(p)
                    inv.table_base = table
                    reported = inv.check_all(all_missions=all_missions)
                    self.assertTrue(all(ALL_LOCATIONS[name].case == case_name
                                        for name in reported), reported)
                    # These first objectives really are arrival milestones.
                    if all_missions and case_name in (
                            SACCases.AZCOTAL_ALLEY, SACCases.HIGH_ROLLERS_CASINO,
                            SACCases.BULKHEAD_LOCK):
                        self.assertIn(CHAPTER_ENTRIES[case_name][0].name, reported)
        self.assertEqual(cross_case, set(NATIVE_FINISH_CASES.values()))
